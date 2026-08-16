"""Unit Tests for Valuation Sensitivity Matrix Calculations."""

import pytest
from app.domains.valuation.engine.sensitivity import SensitivityEngine


def test_wacc_terminal_growth_sensitivity_grid():
    """Verify deterministic 5x5 sensitivity matrix generation for WACC vs Terminal Growth."""
    projections = [
        {"period": "FY2024", "ebit": 10000000.0, "tax_rate": 25.0, "depreciation_amortization": 2000000.0, "capex": 2000000.0, "working_capital_change": 500000.0},
        {"period": "FY2025", "ebit": 12000000.0, "tax_rate": 25.0, "depreciation_amortization": 2200000.0, "capex": 2200000.0, "working_capital_change": 600000.0},
    ]
    grid = SensitivityEngine.generate_wacc_terminal_growth_matrix(
        projections=projections,
        base_wacc=9.0,
        base_growth=3.0,
        matrix_size=5,
    )
    assert grid["type"] == "WACC_VS_TERMINAL_GROWTH"
    assert len(grid["row_values"]) == 5
    assert len(grid["column_values"]) == 5
    assert len(grid["enterprise_value_matrix"]) == 5
    assert len(grid["enterprise_value_matrix"][0]) == 5
    # Base cell is at (2, 2)
    assert grid["enterprise_value_matrix"][2][2] is not None
    assert grid["enterprise_value_matrix"][2][2] > 0


def test_wacc_exit_multiple_sensitivity_grid():
    """Verify deterministic 5x5 sensitivity matrix for WACC vs Exit EBITDA Multiple."""
    projections = [
        {"period": "FY2024", "ebit": 10000000.0, "depreciation_amortization": 2000000.0, "ebitda": 12000000.0},
        {"period": "FY2025", "ebit": 12000000.0, "depreciation_amortization": 2200000.0, "ebitda": 14200000.0},
    ]
    grid = SensitivityEngine.generate_wacc_exit_multiple_matrix(
        projections=projections,
        base_wacc=9.0,
        base_multiple=10.0,
        matrix_size=5,
    )
    assert grid["type"] == "WACC_VS_EXIT_MULTIPLE"
    assert grid["enterprise_value_matrix"][2][2] is not None
