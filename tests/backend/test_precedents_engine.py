"""Unit Tests for Precedent Transactions Analysis (PTA) Engine."""

import pytest
from app.domains.valuation.engine.precedents import PrecedentEngine


def test_precedent_transaction_multiples():
    """Verify transaction multiple derivation for M&A deal."""
    tx = {
        "target_name": "Target Tech",
        "enterprise_value": 500000000.0,
        "revenue": 100000000.0,
        "ebitda": 25000000.0,
    }
    res = PrecedentEngine.calculate_deal_multiples(tx)
    assert res["ev_to_revenue"] == 5.0   # 500M / 100M = 5.0x
    assert res["ev_to_ebitda"] == 20.0  # 500M / 25M = 20.0x


def test_precedent_cohort_statistics():
    """Verify statistical summary across precedent M&A deals."""
    transactions = [
        {"target_name": "Deal 1", "enterprise_value": 150000000.0, "revenue": 30000000.0, "ebitda": 10000000.0, "status": "INCLUDED"},  # 5.0x rev, 15.0x ebitda
        {"target_name": "Deal 2", "enterprise_value": 300000000.0, "revenue": 50000000.0, "ebitda": 15000000.0, "status": "INCLUDED"},  # 6.0x rev, 20.0x ebitda
        {"target_name": "Deal 3", "enterprise_value": 400000000.0, "revenue": 50000000.0, "ebitda": 16000000.0, "status": "INCLUDED"},  # 8.0x rev, 25.0x ebitda
    ]
    stats = PrecedentEngine.calculate_precedent_cohort_statistics(transactions)
    assert stats["included_transactions"] == 3
    assert stats["ev_to_revenue_stats"]["median"] == 6.0
    assert stats["ev_to_ebitda_stats"]["median"] == 20.0
