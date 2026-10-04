"""Tests for the local inference runtime (TTFT and prefill accounting).

The streaming ``genera_bozza`` path is exercised with a stub llama-cpp
client that simulates the first-token delay; the wall-clock delta must
match the real time the engine takes to emit the first chunk. The
fallback path (no chunks at all) is covered too.
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterator
from typing import Any

import pytest

from core.engine import LocalNeuralEngine, OutputInferenza


class _FakeLlamaStream:
    """Stub that mimics llama-cpp's ``Llama.__call__(stream=True)``."""

    def __init__(
        self,
        first_chunk_delay: float = 0.05,
        per_chunk_delay: float = 0.005,
        chunks: int = 4,
        emit_usage_on_last: bool = True,
    ) -> None:
        self.first_chunk_delay = first_chunk_delay
        self.per_chunk_delay = per_chunk_delay
        self.chunks = chunks
        self.emit_usage_on_last = emit_usage_on_last
        self.calls: list[dict[str, object]] = []

    def __call__(self, prompt: str, **kwargs: Any) -> Any:
        self.calls.append({"prompt": prompt, **kwargs})
        if kwargs.get("stream"):
            return self._iter()
        # Non-streaming path: the stub still respects ``first_chunk_delay``
        # so the wall-clock duration is consistent with the streaming
        # case the test cares about.
        time.sleep(self.first_chunk_delay + self.per_chunk_delay * self.chunks)
        return {
            "choices": [{"text": "stubbed answer"}],
            "usage": {"prompt_tokens": 8, "completion_tokens": self.chunks},
        }

    def tokenize(self, text: bytes, **kwargs: Any) -> list[int]:
        return list(range(len(re.findall(r"chunk\d+|\w+", text.decode()))))

    def _iter(self) -> Iterator[dict[str, Any]]:
        for index in range(self.chunks):
            if index == 0:
                time.sleep(self.first_chunk_delay)
            else:
                time.sleep(self.per_chunk_delay)
            chunk: dict[str, Any] = {"choices": [{"text": f"chunk{index}"}]}
            if self.emit_usage_on_last and index == self.chunks - 1:
                chunk["usage"] = {
                    "prompt_tokens": 8,
                    "completion_tokens": self.chunks,
                }
            yield chunk


def _costruisci_engine_stub(stub: _FakeLlamaStream) -> LocalNeuralEngine:
    engine = LocalNeuralEngine.__new__(LocalNeuralEngine)
    engine.llm = stub  # type: ignore[assignment]
    return engine


def test_genera_bozza_misura_ttft_dal_primo_chunk() -> None:
    """The first chunk's wall-clock delay is recorded as ``tempo_prefill_reale_sec``."""
    stub = _FakeLlamaStream(first_chunk_delay=0.04, per_chunk_delay=0.005, chunks=3)
    engine = _costruisci_engine_stub(stub)
    output = engine.genera_bozza("public context", "public question", max_tokens=16)
    assert isinstance(output, OutputInferenza)
    assert output.tempo_prefill_reale_sec is not None
    assert output.tempo_prefill_reale_sec >= 0.04
    # The fallback total duration is dominated by the chunk count.
    assert output.durata_totale_sec >= output.tempo_prefill_reale_sec
    assert output.completion_tokens == 3
    assert output.prompt_tokens == 8
    assert output.testo == "chunk0chunk1chunk2"


def test_genera_bozza_testo_vuoto_cade_su_none() -> None:
    """When llama-cpp yields no chunks the real TTFT is ``None``."""
    stub = _FakeLlamaStream(chunks=0)
    engine = _costruisci_engine_stub(stub)
    output = engine.genera_bozza("public context", "public question", max_tokens=8)
    assert output.tempo_prefill_reale_sec is None
    assert output.testo == ""
    assert len(stub.calls) == 1
    assert output.completion_tokens == 0


def test_genera_bozza_senza_usage_non_ripete_inferenza() -> None:
    """Missing usage must never cause a second neural generation."""

    class _NoUsageStream(_FakeLlamaStream):
        def _iter(self) -> Iterator[dict[str, Any]]:
            for index in range(self.chunks):
                time.sleep(self.per_chunk_delay)
                yield {"choices": [{"text": f"chunk{index}"}]}  # no usage key

    stub = _NoUsageStream(chunks=2)
    engine = _costruisci_engine_stub(stub)
    output = engine.genera_bozza("ctx", "domanda", max_tokens=8)
    assert output.testo == "chunk0chunk1"
    assert output.completion_tokens == 2
    assert len(stub.calls) == 1
    assert stub.calls[0]["stream"] is True
    assert output.token_counts_source == "retokenized_text"
    assert output.prompt_tokens > 0


def test_usage_presente_nel_primo_e_unico_chunk():
    stub = _FakeLlamaStream(chunks=1)
    output = _costruisci_engine_stub(stub).genera_bozza("ctx", "question")
    assert output.prompt_tokens == 8
    assert output.completion_tokens == 1
    assert output.token_counts_source == "backend_usage"
    assert len(stub.calls) == 1


def test_chunk_vuoti_non_anticipano_il_primo_testo():
    class _EmptyFirst(_FakeLlamaStream):
        def _iter(self):
            yield {"choices": [{"text": ""}]}
            time.sleep(0.03)
            yield {"choices": [{"text": "chunk0"}]}

    stub = _EmptyFirst()
    output = _costruisci_engine_stub(stub).genera_bozza("ctx", "question")
    assert output.tempo_prefill_reale_sec >= .03
    assert len(stub.calls) == 1


def test_genera_bozza_rifiuta_max_tokens_non_positivo() -> None:
    stub = _FakeLlamaStream()
    engine = _costruisci_engine_stub(stub)
    with pytest.raises(ValueError):
        engine.genera_bozza("ctx", "domanda", max_tokens=0)
