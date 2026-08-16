"""Unit Tests for Quality of Earnings (QoE) EBITDA Normalization Engine."""

import pytest
from app.domains.financials.engine.qoe import QoEEngine


def test_qoe_bridge_calculation_with_approved_and_proposed():
    """Verify add-backs, deductions, and status filtering."""
    reported_ebitda = 9100000.0  # $9.1M

    adjustments = [
        {
            "category": "LEGAL_NON_RECURRING",
            "description": "One-time litigation defense fees",
            "amount": 450000.0,
            "treatment": "ADD_BACK",
            "status": "APPROVED",
        },
        {
            "category": "OWNER_PERSONAL",
            "description": "Founder personal travel expenses",
            "amount": 300000.0,
            "treatment": "ADD_BACK",
            "status": "APPROVED",
        },
        {
            "category": "ONE_TIME_INCOME",
            "description": "Gain on sale of legacy domain names",
            "amount": 150000.0,
            "treatment": "DEDUCTION",
            "status": "APPROVED",
        },
        {
            "category": "PRO_FORMA",
            "description": "Unverified vendor synergy savings",
            "amount": 500000.0,
            "treatment": "ADD_BACK",
            "status": "PROPOSED",  # Unapproved
        },
    ]

    # Only approved
    bridge = QoEEngine.calculate_adjusted_ebitda(reported_ebitda, adjustments, only_approved=True)
    assert bridge["reported_ebitda"] == 9100000.0
    assert bridge["total_add_backs"] == 750000.0  # 450k + 300k
    assert bridge["total_deductions"] == 150000.0
    assert bridge["net_adjustment"] == 600000.0
    assert bridge["adjusted_ebitda"] == 9700000.0
    assert bridge["applied_adjustments_count"] == 3

    # All including proposed
    all_bridge = QoEEngine.calculate_adjusted_ebitda(reported_ebitda, adjustments, only_approved=False)
    assert all_bridge["total_add_backs"] == 1250000.0
    assert all_bridge["adjusted_ebitda"] == 10200000.0


def test_qoe_bridge_handles_none_ebitda():
    """Verify QoE engine handles missing reported EBITDA gracefully."""
    bridge = QoEEngine.calculate_adjusted_ebitda(None, [])
    assert bridge["reported_ebitda"] is None
    assert bridge["adjusted_ebitda"] is None
