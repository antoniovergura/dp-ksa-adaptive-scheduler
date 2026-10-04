"""Direct timing, public refresh and planning reserves without a model/provider."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from core.cloud import CloudGenerator
from core.latency import LocalLatencyProfile, PublicLatencyRefresh, calibrate_latency
from core.pipeline import RequestConfig, run_request
from core.scheduler import AdaptiveScheduler


def profile(expected=1000, planning=1500):
    return LocalLatencyProfile(1000, 30, expected, planning, (expected, planning),
                               (999, 1000), (5, 30), 100)


def test_complete_inference_cost_includes_truncation(monkeypatch):
    now = [0.0]
    monkeypatch.setattr('core.latency.time.perf_counter', lambda: now[0])
    calls = []

    class Engine:
        def limita_contesto(self, context, query, budget, max_tokens):
            now[0] += 0.2
            calls.append((context, query, budget, max_tokens))
            return 'public'

        def genera_bozza(self, context, query, max_tokens):
            now[0] += len(calls)
            return SimpleNamespace(prompt_tokens=1000, completion_tokens=30,
                                   tempo_prefill_stimato_sec=999999)

    result = calibrate_latency(Engine(), probes=3)
    assert result.samples_ms == pytest.approx((1200, 2200, 3200))
    assert result.expected_ms == pytest.approx(2200)
    assert result.planning_ms == pytest.approx(3200)
    assert result.output_cap_observed
    assert len({c[0] for c in calls}) == 3
    assert all(c[2:] == (1000, 30) for c in calls)


def test_reserve_changes_capacity_but_exposes_expected_time():
    decision = AdaptiveScheduler().schedule(
        [1000] * 40, epsilon_budget=1, latenza_massima_ms=10000,
        e2e_cloud_ms=2000, cloud_expected_ms=1000, overhead_ms=500,
        local_latency_profile=profile(),
    )
    assert decision.n_ensemble == 5
    assert decision.tempo_stimato_ms == 10000
    assert decision.tempo_atteso_ms == 6500
    assert decision.margine_stima_ms == 3500
    assert decision.sla_fattibile


@pytest.mark.parametrize('budget,max_tokens', [(999, 30), (1000, 31)])
def test_profile_cannot_be_reused_for_different_public_caps(budget, max_tokens):
    with pytest.raises(ValueError, match='incompatibile'):
        AdaptiveScheduler(max_tokens=max_tokens).schedule(
            [budget] * 40, epsilon_budget=1, local_latency_profile=profile())


def test_impossible_cloud_budget_is_reported_even_for_zero_shot():
    decision = AdaptiveScheduler().schedule(
        [1000] * 40, epsilon_budget=1, latenza_massima_ms=1000,
        e2e_cloud_ms=2000, local_latency_profile=profile())
    assert decision.n_ensemble == 0
    assert not decision.sla_fattibile
    assert decision.sforamento_previsto_ms == 1000


def test_fixed_baseline_and_tolerance_use_same_planning_estimate():
    kwargs = dict(token_per_documento=[1000] * 40, epsilon_budget=1,
                  latenza_massima_ms=9000, e2e_cloud_ms=2000,
                  local_latency_profile=profile())
    fixed = AdaptiveScheduler().schedule(**kwargs, fixed_n=20)
    assert fixed.n_ensemble == 20 and not fixed.sla_fattibile
    accepted = AdaptiveScheduler().schedule(**kwargs, k_sforamento=0.25)
    assert accepted.n_ensemble == 5 and accepted.sforamento_accettato
    assert accepted.sforamento_previsto_ms == 500


def test_refresh_updates_between_public_request_slots(monkeypatch):
    refresh = PublicLatencyRefresh(every=2)
    initial, slower = profile(), profile(2000, 3000)
    calls = []

    def calibrate(engine, **kwargs):
        calls.append(kwargs)
        return slower

    monkeypatch.setattr('core.latency.calibrate_latency', calibrate)
    for _ in range(2):
        result, info = refresh.before_request(object(), initial)
        assert result == initial and not info['performed']
    result, info = refresh.before_request(object(), initial)
    assert result == slower and info['performed']
    assert calls == [dict(prompt_token_budget=1000, max_tokens=30, probes=3, offset=6)]


def test_failed_refresh_retains_profile_without_retry_storm(monkeypatch):
    refresh = PublicLatencyRefresh(every=2)

    def fail(*args, **kwargs):
        raise RuntimeError('unavailable')

    monkeypatch.setattr('core.latency.calibrate_latency', fail)
    initial = profile()
    for _ in range(2):
        refresh.before_request(None, initial)
    result, info = refresh.before_request(None, initial)
    assert result == initial and info['error'] == 'public_calibration_failed'
    assert not refresh.before_request(None, initial)[1]['performed']


def test_refresh_disabled_does_not_run(monkeypatch):
    monkeypatch.setattr('core.latency.calibrate_latency', lambda *a, **k: pytest.fail())
    refresh = PublicLatencyRefresh(every=0)
    for _ in range(10):
        assert not refresh.before_request(None, profile())[1]['performed']


def test_representative_cloud_probe_uses_real_generation_path(monkeypatch):
    calls = []
    durations = iter([2, 10, 6])
    cloud = CloudGenerator(api_key='synthetic')

    def generate(query, keywords, contexts):
        calls.append((query, keywords, contexts))
        return SimpleNamespace(errore=None, simulato=False,
                               latenza_rete_sec=next(durations))

    monkeypatch.setattr(cloud, 'genera', generate)
    result = cloud.probe_representative()
    assert result.e2e_cloud_ms == 10000
    assert result.expected_ms == 6000
    assert all('pubblica' in query and contexts == [] for query, _, contexts in calls)
    assert any(not keywords for _, keywords, _ in calls)


def test_representative_cloud_failure_does_not_use_partial_fast_results(monkeypatch):
    cloud = CloudGenerator(api_key='synthetic')
    responses = iter([
        SimpleNamespace(errore=None, simulato=False, latenza_rete_sec=1),
        SimpleNamespace(errore='empty_response', simulato=False),
    ])
    monkeypatch.setattr(cloud, 'genera', lambda *a: next(responses))
    result = cloud.probe_representative()
    assert result.e2e_cloud_ms is None and result.cloud_probe_skipped
    assert result.errore == 'empty_response'


def test_offline_probe_never_calls_provider(monkeypatch):
    cloud = CloudGenerator(api_key='synthetic', offline=True)
    monkeypatch.setattr(cloud, 'genera', lambda *a: pytest.fail())
    assert cloud.probe_representative().simulato


def test_private_corpus_cannot_affect_zero_shot_decision():
    class ForbiddenCorpus:
        def retrieve(self, *args):
            pytest.fail('scheduler must decide before retrieval')
    config = RequestConfig(sla_ms=10, local_latency_profile=profile(), e2e_cloud_ms=0)
    result = run_request('public', ForbiddenCorpus(), config, CloudGenerator(offline=True))
    assert result['decision']['n_ensemble'] == 0
    assert result['decision']['fonte_stima'] == 'public_direct'


def test_repl_refresh_reaches_pipeline_and_does_not_change_privacy(monkeypatch):
    from core.documents import DocumentCorpus
    from repl_interattiva import ReplSession
    config = RequestConfig(local_latency_profile=profile(), e2e_cloud_ms=0, sla_ms=10000)
    session = ReplSession(DocumentCorpus([]), config, CloudGenerator(offline=True),
                          engine=object(), recalibrate_every=1)
    first = session.rispondi('public')
    monkeypatch.setattr('core.latency.calibrate_latency', lambda *a, **k: profile(3000, 4000))
    second = session.rispondi('public')
    assert first['decision']['n_ensemble'] >= 5
    assert second['decision']['n_ensemble'] == 0
    assert second['public_recalibration']['performed']
    assert first['decision']['sigma'] == second['decision']['sigma']


@pytest.mark.parametrize('value', [-1, float('nan'), float('inf')])
def test_invalid_overhead_is_rejected(value):
    with pytest.raises(ValueError):
        AdaptiveScheduler().schedule([1000] * 40, epsilon_budget=1, overhead_ms=value)


def test_short_output_coverage_is_explicit():
    assert not replace(profile(), completion_tokens=(2, 3)).output_cap_observed
