"""Unit Tests for Deterministic 3-Statement Modeling & Metric Calculations."""

import pytest
from app.domains.financials.engine.metrics import MetricCalculationEngine
from app.domains.financials.engine.statements import StatementCalculationEngine


def test_income_statement_derivations():
    """Verify deterministic derivation of Gross Profit, EBIT, EBITDA, and Net Income."""
    raw = {
        "revenue": 50000000.0,
        "cogs": 15000000.0,
        "operating_expenses": 20000000.0,
        "depreciation_amortization": 3000000.0,
        "interest_expense": 2000000.0,
        "taxes": 3000000.0,
    }
    res = StatementCalculationEngine.calculate_income_statement(raw)
    assert res["gross_profit"] == 35000000.0
    assert res["ebit"] == 15000000.0
    assert res["ebitda"] == 18000000.0
    assert res["net_income"] == 10000000.0


def test_balance_sheet_derivations_and_balancing():
    """Verify Balance Sheet totals and validation equation (Assets == Liab + Equity)."""
    balanced_raw = {
        "cash": 10000000.0,
        "accounts_receivable": 8000000.0,
        "inventory": 4000000.0,
        "ppe": 20000000.0,
        "accounts_payable": 5000000.0,
        "accrued_liabilities": 2000000.0,
        "long_term_debt": 15000000.0,
        "equity": 20000000.0,
    }
    res = StatementCalculationEngine.calculate_balance_sheet(balanced_raw)
    assert res["total_current_assets"] == 22000000.0
    assert res["total_assets"] == 42000000.0
    assert res["total_current_liabilities"] == 7000000.0
    assert res["total_liabilities"] == 22000000.0
    assert res["total_liabilities_and_equity"] == 42000000.0
    assert res["is_balanced"] is True
    assert res["balance_discrepancy"] == 0.0

    # Unbalanced sheet
    unbalanced_raw = {**balanced_raw, "equity": 15000000.0}
    unbal_res = StatementCalculationEngine.calculate_balance_sheet(unbalanced_raw)
    assert unbal_res["is_balanced"] is False
    assert unbal_res["balance_discrepancy"] == 5000000.0


def test_cash_flow_derivations():
    """Verify Cash Flow Statement CFO, CFI, CFF, and Net Change in Cash."""
    raw = {
        "net_income": 10000000.0,
        "depreciation_amortization": 3000000.0,
        "working_capital_change": 1000000.0,  # Cash outflow
        "capex": 4000000.0,                   # Cash outflow
        "debt_issued": 5000000.0,
        "debt_repaid": 2000000.0,
    }
    res = StatementCalculationEngine.calculate_cash_flow(raw)
    assert res["cash_flow_from_operations"] == 12000000.0
    assert res["cash_flow_from_investing"] == -4000000.0
    assert res["cash_flow_from_financing"] == 3000000.0
    assert res["net_change_in_cash"] == 11000000.0


def test_margin_calculations_and_zero_division():
    """Verify margin calculations handle normal and zero-revenue cases safely."""
    gm = MetricCalculationEngine.calculate_margin(35000000.0, 50000000.0, "GROSS_MARGIN")
    assert gm["value"] == 70.0
    assert gm["is_calculable"] is True

    # Zero revenue
    zero_gm = MetricCalculationEngine.calculate_margin(100.0, 0.0, "GROSS_MARGIN")
    assert zero_gm["value"] is None
    assert zero_gm["is_calculable"] is False


def test_net_debt_and_working_capital():
    """Verify Net Debt and Working Capital metrics."""
    nd = MetricCalculationEngine.calculate_net_debt(total_debt=25000000.0, cash=5000000.0, ebitda=10000000.0)
    assert nd["net_debt"] == 20000000.0
    assert nd["net_debt_to_ebitda"] == 2.0

    wc = MetricCalculationEngine.calculate_working_capital(current_assets=15000000.0, current_liabilities=8000000.0, revenue=50000000.0)
    assert wc["working_capital"] == 7000000.0
    assert wc["working_capital_pct_revenue"] == 14.0


def test_cagr_calculation():
    """Verify multi-year Compound Annual Growth Rate."""
    # $20M to $45M over 3 years: (45/20)^(1/3) - 1 ≈ 31.04%
    cagr = MetricCalculationEngine.calculate_cagr(start_val=20000000.0, end_val=45000000.0, num_years=3)
    assert cagr == 31.04

    # Invalid input
    assert MetricCalculationEngine.calculate_cagr(0, 100, 2) is None
    assert MetricCalculationEngine.calculate_cagr(100, 100, 0) is None


def test_saas_metrics():
    """Verify Rule of 40, CAC Payback, and Net Dollar Retention."""
    r40 = MetricCalculationEngine.calculate_rule_of_40(revenue_growth_pct=28.0, profit_margin_pct=18.0)
    assert r40["value"] == 46.0
    assert r40["passes_benchmark"] is True

    cac_pb = MetricCalculationEngine.calculate_cac_payback(cac=6000.0, arpu_annual=10000.0, gross_margin_pct=80.0)
    assert cac_pb["value"] == 9.0  # 6000 / (10000 * 0.8) * 12 = 9.0 months

    ndr = MetricCalculationEngine.calculate_ndr(cohort_start_arr=10000000.0, cohort_end_arr=11800000.0)
    assert ndr["value"] == 118.0
    assert ndr["is_best_in_class"] is True
