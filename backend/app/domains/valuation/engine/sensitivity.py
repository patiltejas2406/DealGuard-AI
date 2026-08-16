"""Deterministic Multi-Variable Valuation Sensitivity Analysis Engine."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.domains.financials.engine.statements import to_decimal, to_float
from app.domains.valuation.engine.dcf import DCFEngine


class SensitivityEngine:
    """Computes deterministic 2D sensitivity grids for DCF and multiple parameters."""

    @staticmethod
    def generate_wacc_terminal_growth_matrix(
        projections: List[Dict[str, Any]],
        base_wacc: float = 9.0,
        base_growth: float = 3.0,
        cash: float = 0.0,
        debt: float = 0.0,
        minority_interest: float = 0.0,
        preferred_equity: float = 0.0,
        wacc_step: float = 0.5,
        growth_step: float = 0.25,
        matrix_size: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate 2D Grid: WACC (rows) × Terminal Growth Rate (columns) -> Implied Enterprise Value.
        """
        half = matrix_size // 2
        wacc_values = [round(base_wacc + (i - half) * wacc_step, 2) for i in range(matrix_size)]
        growth_values = [round(base_growth + (j - half) * growth_step, 2) for j in range(matrix_size)]

        grid_ev: List[List[Optional[float]]] = []
        grid_equity: List[List[Optional[float]]] = []

        for w_val in wacc_values:
            row_ev: List[Optional[float]] = []
            row_eq: List[Optional[float]] = []
            for g_val in growth_values:
                if w_val <= g_val:
                    row_ev.append(None)
                    row_eq.append(None)
                else:
                    try:
                        dcf_res = DCFEngine.calculate_dcf(
                            projections=projections,
                            wacc=w_val,
                            terminal_growth_rate=g_val,
                            terminal_method="PERPETUITY_GROWTH",
                            cash=cash,
                            debt=debt,
                            minority_interest=minority_interest,
                            preferred_equity=preferred_equity,
                        )
                        row_ev.append(dcf_res["implied_enterprise_value"])
                        row_eq.append(dcf_res["implied_equity_value"])
                    except Exception:
                        row_ev.append(None)
                        row_eq.append(None)
            grid_ev.append(row_ev)
            grid_equity.append(row_eq)

        return {
            "type": "WACC_VS_TERMINAL_GROWTH",
            "row_variable": "WACC (%)",
            "column_variable": "Terminal Growth Rate (%)",
            "row_values": wacc_values,
            "column_values": growth_values,
            "base_row_index": half,
            "base_column_index": half,
            "enterprise_value_matrix": grid_ev,
            "equity_value_matrix": grid_equity,
        }

    @staticmethod
    def generate_wacc_exit_multiple_matrix(
        projections: List[Dict[str, Any]],
        base_wacc: float = 9.0,
        base_multiple: float = 10.0,
        cash: float = 0.0,
        debt: float = 0.0,
        minority_interest: float = 0.0,
        preferred_equity: float = 0.0,
        wacc_step: float = 0.5,
        multiple_step: float = 1.0,
        matrix_size: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate 2D Grid: WACC (rows) × Exit EBITDA Multiple (columns) -> Implied Enterprise Value.
        """
        half = matrix_size // 2
        wacc_values = [round(base_wacc + (i - half) * wacc_step, 2) for i in range(matrix_size)]
        multiple_values = [round(base_multiple + (j - half) * multiple_step, 1) for j in range(matrix_size)]

        grid_ev: List[List[Optional[float]]] = []
        grid_equity: List[List[Optional[float]]] = []

        for w_val in wacc_values:
            row_ev: List[Optional[float]] = []
            row_eq: List[Optional[float]] = []
            for m_val in multiple_values:
                try:
                    dcf_res = DCFEngine.calculate_dcf(
                        projections=projections,
                        wacc=w_val,
                        exit_multiple=m_val,
                        terminal_method="EXIT_MULTIPLE",
                        cash=cash,
                        debt=debt,
                        minority_interest=minority_interest,
                        preferred_equity=preferred_equity,
                    )
                    row_ev.append(dcf_res["implied_enterprise_value"])
                    row_eq.append(dcf_res["implied_equity_value"])
                except Exception:
                    row_ev.append(None)
                    row_eq.append(None)
            grid_ev.append(row_ev)
            grid_equity.append(row_eq)

        return {
            "type": "WACC_VS_EXIT_MULTIPLE",
            "row_variable": "WACC (%)",
            "column_variable": "Exit EBITDA Multiple (x)",
            "row_values": wacc_values,
            "column_values": multiple_values,
            "base_row_index": half,
            "base_column_index": half,
            "enterprise_value_matrix": grid_ev,
            "equity_value_matrix": grid_equity,
        }
