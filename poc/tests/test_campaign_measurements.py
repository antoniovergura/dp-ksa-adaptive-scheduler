"""Campaign guardrails: cumulative accounting and comparable configurations."""
from collections import Counter

import pytest

from campaign_measurements import clean, make_account, make_jobs
from core.pipeline import RequestConfig
from core.privacy import DPBudgetExhaustedError


def test_campaign_accounts_do_not_silently_reset():
    account = make_account(4, 1e-4, 3)
    for _ in range(3):
        account.filtra(['cache servizio'] * 5)
    assert account.numero_invocazioni == 3
    assert account.account.delta_total == pytest.approx(4e-4)
    with pytest.raises(DPBudgetExhaustedError):
        account.verifica_budget()


def test_primary_cloud_comparison_keeps_offline_privacy_parameters():
    tickets = [{'id': str(i), 'query': 'public question'} for i in range(4)]
    salaries = [{'id': 'salary', 'query': 'public salary question'}]
    jobs = make_jobs(RequestConfig(epsilon=4, delta=1e-4), tickets, salaries)
    counts = Counter(job['phase'] for job in jobs)
    assert counts == {'C3_offline': 150, 'C1_cloud': 20, 'C3_cloud': 30,
                      'C3_high_cloud': 30, 'D_cloud': 10}
    for job in jobs:
        if job['phase'] in ('C3_offline', 'C3_cloud'):
            assert (job['config'].epsilon, job['config'].delta) == (4, 1e-4)


def test_missing_sensor_measurements_remain_missing_in_strict_json():
    assert clean({'sample': [float('nan'), float('inf'), 0.0, None]}) == {
        'sample': [None, None, 0.0, None]}
