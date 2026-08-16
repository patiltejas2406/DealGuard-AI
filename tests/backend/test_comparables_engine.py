"""Unit Tests for Trading Comparable Company Analysis (CCA) Engine."""

import pytest
from app.domains.valuation.engine.comparables import ComparableEngine


def test_comparable_multiples_derivation():
    """Verify peer EV/Revenue, EV/EBITDA, and P/E derivation."""
    comp = {
        "company_name": "CloudScale Inc",
        "enterprise_value": 300000000.0,
        "equity_value": 280000000.0,
        "revenue": 50000000.0,
        "ebitda": 15000000.0,
        "net_income": 10000000.0,
    }
    res = ComparableEngine.calculate_comp_multiples(comp)
    assert res["ev_to_revenue"] == 6.0    # 300M / 50M = 6.0x
    assert res["ev_to_ebitda"] == 20.0   # 300M / 15M = 20.0x
    assert res["pe_ratio"] == 28.0       # 280M / 10M = 28.0x


def test_comparable_cohort_statistics_and_inclusion_filter():
    """Verify cohort statistics and filtering of EXCLUDED peers."""
    companies = [
        {"company_name": "Peer A", "enterprise_value": 100000000.0, "revenue": 20000000.0, "ebitda": 5000000.0, "status": "INCLUDED"},   # EV/Rev = 5.0x, EV/EBITDA = 20.0x
        {"company_name": "Peer B", "enterprise_value": 200000000.0, "revenue": 40000000.0, "ebitda": 10000000.0, "status": "INCLUDED"},  # EV/Rev = 5.0x, EV/EBITDA = 20.0x
        {"company_name": "Peer C", "enterprise_value": 400000000.0, "revenue": 50000000.0, "ebitda": 16000000.0, "status": "INCLUDED"},  # EV/Rev = 8.0x, EV/EBITDA = 25.0x
        {"company_name": "Outlier D", "enterprise_value": 900000000.0, "revenue": 30000000.0, "ebitda": 6000000.0, "status": "EXCLUDED"}, # EV/Rev = 30.0x (Excluded)
    ]
    stats = ComparableEngine.calculate_comp_cohort_statistics(companies, only_included=True)
    assert stats["included_companies"] == 3
    assert stats["ev_to_revenue_stats"]["min"] == 5.0
    assert stats["ev_to_revenue_stats"]["median"] == 5.0
    assert stats["ev_to_revenue_stats"]["max"] == 8.0


def test_implied_valuation_range():
    """Verify applying peer multiple stats to target company metric."""
    multiple_stats = {
        "min": 4.0,
        "percentile_25": 5.0,
        "median": 6.0,
        "mean": 6.5,
        "percentile_75": 8.0,
        "max": 10.0,
    }
    # Target EBITDA = $10M, Cash = $2M, Debt = $5M
    res = ComparableEngine.calculate_implied_valuation(
        target_metric_value=10000000.0,
        multiple_stats=multiple_stats,
        metric_type="EBITDA",
        cash=2000000.0,
        debt=5000000.0,
    )
    assert res["is_calculable"] is True
    assert res["implied_enterprise_value_low"] == 50000000.0   # $10M * 5.0x = $50M
    assert res["implied_enterprise_value_base"] == 60000000.0  # $10M * 6.0x = $60M
    assert res["implied_enterprise_value_high"] == 80000000.0  # $10M * 8.0x = $80M
    assert res["implied_equity_value_base"] == 57000000.0      # $60M + 2M - 5M = $57M
