"""Public, session-scoped latency measurements; never learn from private runs.

The observed maximum is an empirical planning reserve, NOT a percentile or a
deadline guarantee. Profiles apply only to their exact public prompt/output caps
and to the preloaded engine used to measure them.
"""
from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class LocalLatencyProfile:
    prompt_token_budget: int
    max_tokens: int
    expected_ms: float
    planning_ms: float
    samples_ms: tuple[float, ...]
    prompt_tokens: tuple[int, ...]
    completion_tokens: tuple[int, ...]
    calibration_ms: float

    def __post_init__(self):
        if self.prompt_token_budget < 1 or self.max_tokens < 1:
            raise ValueError('I limiti pubblici devono essere positivi')
        if not all(math.isfinite(x) and x > 0 for x in (self.expected_ms, self.planning_ms)):
            raise ValueError('Tempi locali positivi e finiti richiesti')
        if self.planning_ms < self.expected_ms:
            raise ValueError('Il tempo prudenziale deve coprire il tempo atteso')

    @property
    def output_cap_observed(self) -> bool:
        # Text retokenization can differ slightly from generated token IDs.
        return max(self.completion_tokens, default=0) >= max(1, self.max_tokens - 2)


def public_probe(index: int, prompt_token_budget: int) -> tuple[str, str]:
    """Vary the early context to avoid an identical cached calibration prefix.

    Eight long identifiers fit the extractor's under-ten-word instruction but
    exercise longer token sequences. All strings are synthetic public constants.
    """
    identifiers = ' '.join(f'modulo-{index + 1:03d}-{j:03d}-alfa' for j in range(8))
    facts = (f'Scheda pubblica {index}: responsabile Ada. '
             f'Componenti in ordine: {identifiers}. '
             'Procedura: arrestare servizio; svuotare cache; riavviare servizio. ')
    filler = ' '.join(f'Nota pubblica {index}-{j}: controllo periodico del sistema.'
                      for j in range(prompt_token_budget))
    query = ('Chi è il responsabile?' if index % 3 == 0
             else 'Copia tutti gli otto identificativi dei componenti in ordine.')
    return facts + filler, query


def calibrate_latency(engine, *, prompt_token_budget=1000, max_tokens=30,
                      probes=6, offset=0) -> LocalLatencyProfile:
    """Measure truncation + complete inference on a sequence of public probes.

    No phase-time splitting, no corpus or real request input. The setup cost is
    returned separately; callers run this outside the timed user request.
    """
    if prompt_token_budget < 1 or max_tokens < 1 or probes < 3:
        raise ValueError('Limiti positivi e almeno tre probe pubblici richiesti')
    started = time.perf_counter()
    durations, inputs, outputs = [], [], []
    for i in range(offset, offset + probes):
        context, query = public_probe(i, prompt_token_budget)
        before = time.perf_counter()
        context = engine.limita_contesto(context, query, prompt_token_budget, max_tokens)
        output = engine.genera_bozza(context, query, max_tokens=max_tokens)
        elapsed = (time.perf_counter() - before) * 1000
        if not math.isfinite(elapsed) or elapsed <= 0:
            raise ValueError('Durata del probe locale non valida')
        durations.append(elapsed)
        inputs.append(output.prompt_tokens)
        outputs.append(output.completion_tokens)
    return LocalLatencyProfile(
        prompt_token_budget, max_tokens, statistics.mean(durations), max(durations),
        tuple(durations), tuple(inputs), tuple(outputs),
        (time.perf_counter() - started) * 1000,
    )


class PublicLatencyRefresh:
    """Refresh after a fixed number of public request slots, never by their times.

    An unsuccessful refresh keeps the last complete profile and is reported.
    A failure consumes a slot interval too, preventing retry storms.
    """

    def __init__(self, every=5):
        if not isinstance(every, int) or every < 0:
            raise ValueError('Intervallo di ricalibrazione intero non negativo richiesto')
        self.every = every
        self.requests = 0
        self.generation = 0

    def before_request(self, engine, profile):
        due = self.every and self.requests > 0 and self.requests % self.every == 0
        self.requests += 1
        if not due or profile is None:
            return profile, {'performed': False, 'elapsed_ms': 0.0}
        started = time.perf_counter()
        self.generation += 1
        try:
            updated = calibrate_latency(
                engine, prompt_token_budget=profile.prompt_token_budget,
                max_tokens=profile.max_tokens, probes=3, offset=6 * self.generation,
            )
            return updated, {'performed': True, 'elapsed_ms': updated.calibration_ms,
                             'error': None}
        except (ValueError, RuntimeError, OSError):
            return profile, {'performed': True,
                             'elapsed_ms': (time.perf_counter() - started) * 1000,
                             'error': 'public_calibration_failed', 'previous_profile_retained': True}
