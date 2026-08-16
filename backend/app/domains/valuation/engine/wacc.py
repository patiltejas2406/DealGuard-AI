"""Deterministic Weighted Average Cost of Capital (WACC) Calculation Engine."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Optional
from app.domains.financials.engine.statements import to_decimal, to_float


class WACCEngine:
    """Computes transparent, auditable Cost of Equity (CAPM), After-Tax Debt, and WACC."""

    @staticmethod
    def calculate_cost_of_equity(
        risk_free_rate: Any,
        beta: Any,
        equity_risk_premium: Any,
    ) -> Dict[str, Any]:
        """
        Cost of Equity (Ke) = Risk-Free Rate + Beta * Equity Risk Premium
        Expected inputs: rates in percentage (e.g. 5.0 for 5.0%) or decimal ratios.
        """
        rf = to_decimal(risk_free_rate)
        b = to_decimal(beta)
        erp = to_decimal(equity_risk_premium)

        missing = []
        if rf is None:
            missing.append("risk_free_rate")
        if b is None:
            missing.append("beta")
        if erp is None:
            missing.append("equity_risk_premium")

        if missing:
            return {
                "cost_of_equity": None,
                "missing_inputs": missing,
                "is_calculable": False,
            }

        # Normalize percentage if entered as ratio (< 1.0)
        rf_pct = rf * Decimal(100) if Decimal(0) < rf < Decimal(1) else rf
        erp_pct = erp * Decimal(100) if Decimal(0) < erp < Decimal(1) else erp

        ke = rf_pct + (b * erp_pct)
        return {
            "risk_free_rate": to_float(rf_pct),
            "beta": to_float(b),
            "equity_risk_premium": to_float(erp_pct),
            "cost_of_equity": to_float(ke, round_digits=2),
            "formula": f"Cost of Equity = {to_float(rf_pct)}% + ({to_float(b)} × {to_float(erp_pct)}%) = {to_float(ke, 2)}%",
            "is_calculable": True,
        }

    @staticmethod
    def calculate_after_tax_cost_of_debt(
        pre_tax_cost_of_debt: Any,
        tax_rate: Any,
    ) -> Dict[str, Any]:
        """
        After-Tax Cost of Debt (Kd) = Pre-Tax Cost of Debt * (1 - Tax Rate)
        """
        kd = to_decimal(pre_tax_cost_of_debt)
        t = to_decimal(tax_rate)

        missing = []
        if kd is None:
            missing.append("pre_tax_cost_of_debt")
        if t is None:
            missing.append("tax_rate")

        if missing:
            return {
                "after_tax_cost_of_debt": None,
                "missing_inputs": missing,
                "is_calculable": False,
            }

        kd_pct = kd * Decimal(100) if Decimal(0) < kd < Decimal(1) else kd
        t_ratio = t / Decimal(100) if t > Decimal(1) else t

        after_tax_kd = kd_pct * (Decimal(1) - t_ratio)
        return {
            "pre_tax_cost_of_debt": to_float(kd_pct),
            "tax_rate": to_float(t_ratio * Decimal(100)),
            "after_tax_cost_of_debt": to_float(after_tax_kd, round_digits=2),
            "formula": f"After-Tax Kd = {to_float(kd_pct)}% × (1 - {to_float(t_ratio * Decimal(100))}%) = {to_float(after_tax_kd, 2)}%",
            "is_calculable": True,
        }

    @staticmethod
    def calculate_wacc(
        risk_free_rate: Any,
        beta: Any,
        equity_risk_premium: Any,
        pre_tax_cost_of_debt: Any,
        tax_rate: Any,
        equity_weight: Any = 80.0,
        debt_weight: Any = 20.0,
    ) -> Dict[str, Any]:
        """
        WACC = (Equity Weight * Cost of Equity) + (Debt Weight * After-Tax Cost of Debt)
        """
        ke_res = WACCEngine.calculate_cost_of_equity(risk_free_rate, beta, equity_risk_premium)
        kd_res = WACCEngine.calculate_after_tax_cost_of_debt(pre_tax_cost_of_debt, tax_rate)

        if not ke_res.get("is_calculable") or not kd_res.get("is_calculable"):
            missing = ke_res.get("missing_inputs", []) + kd_res.get("missing_inputs", [])
            return {
                "wacc": None,
                "cost_of_equity": ke_res.get("cost_of_equity"),
                "after_tax_cost_of_debt": kd_res.get("after_tax_cost_of_debt"),
                "missing_inputs": list(set(missing)),
                "is_calculable": False,
            }

        ew_d = to_decimal(equity_weight) or Decimal(80)
        dw_d = to_decimal(debt_weight) or Decimal(20)

        # Normalize weights to sum to 1.0
        total_w = ew_d + dw_d
        if total_w <= Decimal(0):
            ew_ratio = Decimal("0.80")
            dw_ratio = Decimal("0.20")
        else:
            ew_ratio = ew_d / total_w
            dw_ratio = dw_d / total_w

        ke_val = Decimal(str(ke_res["cost_of_equity"]))
        kd_val = Decimal(str(kd_res["after_tax_cost_of_debt"]))

        wacc = (ew_ratio * ke_val) + (dw_ratio * kd_val)
        return {
            "wacc": to_float(wacc, round_digits=2),
            "cost_of_equity": to_float(ke_val, round_digits=2),
            "after_tax_cost_of_debt": to_float(kd_val, round_digits=2),
            "equity_weight": to_float(ew_ratio * Decimal(100), round_digits=1),
            "debt_weight": to_float(dw_ratio * Decimal(100), round_digits=1),
            "components": {
                "cost_of_equity_details": ke_res,
                "cost_of_debt_details": kd_res,
            },
            "formula": f"WACC = ({to_float(ew_ratio * 100, 1)}% × {to_float(ke_val, 2)}%) + ({to_float(dw_ratio * 100, 1)}% × {to_float(kd_val, 2)}%) = {to_float(wacc, 2)}%",
            "is_calculable": True,
        }
