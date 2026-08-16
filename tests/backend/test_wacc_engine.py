"""Unit Tests for Deterministic WACC & CAPM Calculation Engine."""

import pytest
from app.domains.valuation.engine.wacc import WACCEngine


def test_cost_of_equity_capm():
    """Verify CAPM Cost of Equity = Rf + Beta * ERP."""
    # Rf = 4.5%, Beta = 1.2, ERP = 5.5% -> Ke = 4.5 + (1.2 * 5.5) = 11.10%
    res = WACCEngine.calculate_cost_of_equity(risk_free_rate=4.5, beta=1.2, equity_risk_premium=5.5)
    assert res["is_calculable"] is True
    assert res["cost_of_equity"] == 11.10


def test_after_tax_cost_of_debt():
    """Verify After-Tax Kd = Pre-Tax Kd * (1 - Tax Rate)."""
    # Pre-Tax Kd = 6.0%, Tax Rate = 25.0% -> After-Tax Kd = 6.0 * (1 - 0.25) = 4.50%
    res = WACCEngine.calculate_after_tax_cost_of_debt(pre_tax_cost_of_debt=6.0, tax_rate=25.0)
    assert res["is_calculable"] is True
    assert res["after_tax_cost_of_debt"] == 4.50


def test_wacc_calculation_and_weight_normalization():
    """Verify WACC = (We * Ke) + (Wd * Kd_after_tax)."""
    # Ke = 11.10%, Kd_after_tax = 4.50%
    # Weights: Equity = 80%, Debt = 20% -> WACC = (0.8 * 11.10) + (0.2 * 4.50) = 8.88 + 0.90 = 9.78%
    res = WACCEngine.calculate_wacc(
        risk_free_rate=4.5,
        beta=1.2,
        equity_risk_premium=5.5,
        pre_tax_cost_of_debt=6.0,
        tax_rate=25.0,
        equity_weight=80.0,
        debt_weight=20.0,
    )
    assert res["is_calculable"] is True
    assert res["cost_of_equity"] == 11.10
    assert res["after_tax_cost_of_debt"] == 4.50
    assert res["wacc"] == 9.78


def test_wacc_handles_missing_inputs():
    """Verify WACC reports missing inputs cleanly without crashing."""
    res = WACCEngine.calculate_wacc(
        risk_free_rate=None,
        beta=1.2,
        equity_risk_premium=5.5,
        pre_tax_cost_of_debt=6.0,
        tax_rate=25.0,
    )
    assert res["is_calculable"] is False
    assert res["wacc"] is None
    assert "risk_free_rate" in res["missing_inputs"]
