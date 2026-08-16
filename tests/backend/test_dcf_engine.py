"""Unit Tests for Deterministic DCF, UFCF, and Terminal Value Calculations."""

import pytest
from app.core.exceptions import ValidationException
from app.domains.valuation.engine.dcf import DCFEngine


def test_ufcf_derivation():
    """Verify Unlevered Free Cash Flow (UFCF) = EBIT * (1 - t) + D&A - CapEx - Delta WC."""
    # EBIT = $10M, Tax Rate = 25% -> NOPAT = $7.5M
    # D&A = $2M, CapEx = $3M, Delta WC = $1M -> UFCF = 7.5 + 2 - 3 - 1 = $5.5M
    res = DCFEngine.calculate_ufcf(
        ebit=10000000.0,
        tax_rate=25.0,
        depreciation_amortization=2000000.0,
        capex=3000000.0,
        working_capital_change=1000000.0,
    )
    assert res["is_calculable"] is True
    assert res["nopat"] == 7500000.0
    assert res["ufcf"] == 5500000.0


def test_dcf_perpetuity_growth_and_equity_bridge():
    """Verify multi-period DCF schedule, perpetuity growth Terminal Value, EV, and Equity Value."""
    projections = [
        {"period": "FY2024", "ebit": 10000000.0, "tax_rate": 25.0, "depreciation_amortization": 2000000.0, "capex": 2500000.0, "working_capital_change": 1000000.0},
        {"period": "FY2025", "ebit": 12000000.0, "tax_rate": 25.0, "depreciation_amortization": 2200000.0, "capex": 2700000.0, "working_capital_change": 1100000.0},
        {"period": "FY2026", "ebit": 14000000.0, "tax_rate": 25.0, "depreciation_amortization": 2500000.0, "capex": 3000000.0, "working_capital_change": 1200000.0},
    ]
    # WACC = 10.0%, Terminal Growth = 3.0%
    res = DCFEngine.calculate_dcf(
        projections=projections,
        wacc=10.0,
        terminal_growth_rate=3.0,
        terminal_method="PERPETUITY_GROWTH",
        cash=5000000.0,
        debt=15000000.0,
    )
    assert len(res["schedule"]) == 3
    assert res["pv_forecast_fcf"] > 0
    assert res["terminal_value"] > 0
    assert res["implied_enterprise_value"] > 0
    # Implied Equity Value = Implied EV + $5M cash - $15M debt = Implied EV - $10M
    expected_equity = res["implied_enterprise_value"] - 10000000.0
    assert abs(res["implied_equity_value"] - expected_equity) < 0.05


def test_dcf_exit_multiple_method():
    """Verify Exit Multiple Terminal Value = Final EBITDA * Multiple."""
    projections = [
        {"period": "FY2024", "ebit": 10000000.0, "depreciation_amortization": 2000000.0, "ebitda": 12000000.0},
        {"period": "FY2025", "ebit": 12000000.0, "depreciation_amortization": 3000000.0, "ebitda": 15000000.0},
    ]
    res = DCFEngine.calculate_dcf(
        projections=projections,
        wacc=9.0,
        exit_multiple=10.0,
        terminal_method="EXIT_MULTIPLE",
    )
    assert res["terminal_value"] == 150000000.0  # $15M EBITDA * 10x = $150M


def test_dcf_rejects_invalid_wacc_terminal_growth():
    """Verify DCF throws ValidationException when WACC <= Terminal Growth Rate."""
    projections = [{"period": "FY2024", "ebit": 10000000.0}]
    with pytest.raises(ValidationException, match="must be strictly greater"):
        DCFEngine.calculate_dcf(
            projections=projections,
            wacc=3.0,
            terminal_growth_rate=3.0,
            terminal_method="PERPETUITY_GROWTH",
        )
