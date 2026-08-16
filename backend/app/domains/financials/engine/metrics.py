"""Deterministic Financial Ratio & SaaS Metric Calculation Engine."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from app.domains.financials.engine.statements import to_decimal, to_float


class MetricCalculationEngine:
    """Computes deterministic profitability margins, leverage ratios, liquidity, and SaaS metrics."""

    @staticmethod
    def calculate_margin(numerator: Any, revenue: Any, metric_name: str) -> Dict[str, Any]:
        """Calculate margin percentage with zero-denominator and missing-value protection."""
        num_d = to_decimal(numerator)
        rev_d = to_decimal(revenue)

        if num_d is None or rev_d is None:
            missing = []
            if num_d is None:
                missing.append("numerator")
            if rev_d is None:
                missing.append("revenue")
            return {
                "metric_name": metric_name,
                "value": None,
                "unit": "PERCENTAGE",
                "formula": f"{metric_name} = numerator / revenue",
                "missing_inputs": missing,
                "is_calculable": False,
            }

        if rev_d == Decimal(0):
            return {
                "metric_name": metric_name,
                "value": None,
                "unit": "PERCENTAGE",
                "formula": f"{metric_name} = numerator / revenue",
                "error": "Division by zero (revenue is zero)",
                "is_calculable": False,
            }

        margin = (num_d / rev_d) * Decimal(100)
        return {
            "metric_name": metric_name,
            "value": to_float(margin, round_digits=2),
            "unit": "PERCENTAGE",
            "formula": f"{metric_name} = ({to_float(num_d)} / {to_float(rev_d)}) * 100",
            "is_calculable": True,
        }

    @staticmethod
    def calculate_net_debt(total_debt: Any, cash: Any, ebitda: Any = None) -> Dict[str, Any]:
        """Calculate Net Debt = Total Debt - Cash, and Net Debt / EBITDA leverage."""
        debt_d = to_decimal(total_debt)
        cash_d = to_decimal(cash)
        ebitda_d = to_decimal(ebitda)

        if debt_d is None or cash_d is None:
            missing = []
            if debt_d is None:
                missing.append("total_debt")
            if cash_d is None:
                missing.append("cash")
            return {
                "net_debt": None,
                "net_debt_to_ebitda": None,
                "missing_inputs": missing,
            }

        net_debt = debt_d - cash_d

        leverage = None
        if ebitda_d is not None and ebitda_d > Decimal(0):
            leverage = to_float(net_debt / ebitda_d, round_digits=2)

        return {
            "net_debt": to_float(net_debt, round_digits=2),
            "net_debt_to_ebitda": leverage,
            "formula_net_debt": "Total Debt - Cash",
            "formula_leverage": "Net Debt / EBITDA",
        }

    @staticmethod
    def calculate_working_capital(current_assets: Any, current_liabilities: Any, revenue: Any = None) -> Dict[str, Any]:
        """Calculate Working Capital = Current Assets - Current Liabilities, and % of Revenue."""
        ca_d = to_decimal(current_assets)
        cl_d = to_decimal(current_liabilities)
        rev_d = to_decimal(revenue)

        if ca_d is None or cl_d is None:
            return {
                "working_capital": None,
                "working_capital_pct_revenue": None,
                "missing_inputs": ["current_assets" if ca_d is None else "current_liabilities"],
            }

        wc = ca_d - cl_d
        wc_pct = None
        if rev_d is not None and rev_d > Decimal(0):
            wc_pct = to_float((wc / rev_d) * Decimal(100), round_digits=2)

        return {
            "working_capital": to_float(wc, round_digits=2),
            "working_capital_pct_revenue": wc_pct,
            "formula": "Total Current Assets - Total Current Liabilities",
        }

    @staticmethod
    def calculate_cagr(start_val: Any, end_val: Any, num_years: int) -> Optional[float]:
        """Calculate Compound Annual Growth Rate (CAGR)."""
        start_d = to_decimal(start_val)
        end_d = to_decimal(end_val)

        if start_d is None or end_d is None or num_years <= 0 or start_d <= Decimal(0) or end_d <= Decimal(0):
            return None

        # CAGR = (End / Start) ^ (1 / n) - 1
        ratio = float(end_d / start_d)
        cagr = (ratio ** (1.0 / num_years)) - 1.0
        return round(cagr * 100.0, 2)

    @staticmethod
    def calculate_rule_of_40(revenue_growth_pct: Any, profit_margin_pct: Any) -> Dict[str, Any]:
        """Rule of 40 = Revenue Growth Rate (%) + EBITDA Margin (%) or FCF Margin (%)."""
        growth_d = to_decimal(revenue_growth_pct)
        margin_d = to_decimal(profit_margin_pct)

        if growth_d is None or margin_d is None:
            return {
                "metric_name": "RULE_OF_40",
                "value": None,
                "unit": "SCORE",
                "missing_inputs": ["revenue_growth_pct" if growth_d is None else "profit_margin_pct"],
                "passes_benchmark": None,
            }

        score = growth_d + margin_d
        score_val = to_float(score, round_digits=2)
        return {
            "metric_name": "RULE_OF_40",
            "value": score_val,
            "unit": "SCORE",
            "formula": f"Revenue Growth ({to_float(growth_d)}%) + Profit Margin ({to_float(margin_d)}%)",
            "passes_benchmark": score_val is not None and score_val >= 40.0,
        }

    @staticmethod
    def calculate_cac_payback(cac: Any, arpu_annual: Any, gross_margin_pct: Any) -> Dict[str, Any]:
        """Calculate CAC Payback Period in Months = CAC / (Annual ARPU * Gross Margin %) * 12."""
        cac_d = to_decimal(cac)
        arpu_d = to_decimal(arpu_annual)
        gm_d = to_decimal(gross_margin_pct)

        if cac_d is None or arpu_d is None or gm_d is None:
            return {
                "metric_name": "CAC_PAYBACK_MONTHS",
                "value": None,
                "unit": "MONTHS",
                "missing_inputs": ["cac" if cac_d is None else ("arpu_annual" if arpu_d is None else "gross_margin_pct")],
            }

        gm_ratio = gm_d / Decimal(100) if gm_d > Decimal(1) else gm_d
        gross_profit_per_user = arpu_d * gm_ratio

        if gross_profit_per_user <= Decimal(0):
            return {
                "metric_name": "CAC_PAYBACK_MONTHS",
                "value": None,
                "unit": "MONTHS",
                "error": "Gross profit per customer is zero or negative",
            }

        payback_months = (cac_d / gross_profit_per_user) * Decimal(12)
        return {
            "metric_name": "CAC_PAYBACK_MONTHS",
            "value": to_float(payback_months, round_digits=1),
            "unit": "MONTHS",
            "formula": "CAC / (ARPU * Gross Margin) * 12",
        }

    @staticmethod
    def calculate_ndr(cohort_start_arr: Any, cohort_end_arr: Any) -> Dict[str, Any]:
        """Calculate Net Dollar Retention (NDR) = (Cohort Ending ARR / Cohort Starting ARR) * 100."""
        start_d = to_decimal(cohort_start_arr)
        end_d = to_decimal(cohort_end_arr)

        if start_d is None or end_d is None:
            return {
                "metric_name": "NET_DOLLAR_RETENTION",
                "value": None,
                "unit": "PERCENTAGE",
                "missing_inputs": ["cohort_start_arr" if start_d is None else "cohort_end_arr"],
            }

        if start_d == Decimal(0):
            return {
                "metric_name": "NET_DOLLAR_RETENTION",
                "value": None,
                "unit": "PERCENTAGE",
                "error": "Starting ARR is zero",
            }

        ndr = (end_d / start_d) * Decimal(100)
        return {
            "metric_name": "NET_DOLLAR_RETENTION",
            "value": to_float(ndr, round_digits=2),
            "unit": "PERCENTAGE",
            "formula": "(Ending Cohort ARR / Starting Cohort ARR) * 100",
            "is_best_in_class": to_float(ndr) >= 115.0 if ndr else False,
        }
