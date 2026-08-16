"""Trading Comparable Company Analysis (CCA) Calculation Engine."""

import statistics
from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.domains.financials.engine.statements import to_decimal, to_float
from app.domains.valuation.engine.bridge import ValuationBridgeEngine


class ComparableEngine:
    """Computes trading peer valuation multiples, statistical percentiles, and implied EV/Equity values."""

    @staticmethod
    def calculate_comp_multiples(comp: Dict[str, Any]) -> Dict[str, Any]:
        """Derive EV/Revenue, EV/EBITDA, and P/E multiples for a single peer company."""
        ev_d = to_decimal(comp.get("enterprise_value"))
        eq_d = to_decimal(comp.get("equity_value"))
        rev_d = to_decimal(comp.get("revenue"))
        ebitda_d = to_decimal(comp.get("ebitda"))
        ni_d = to_decimal(comp.get("net_income"))

        ev_to_rev = None
        if ev_d is not None and rev_d is not None and rev_d > Decimal(0):
            ev_to_rev = to_float(ev_d / rev_d, round_digits=2)

        ev_to_ebitda = None
        if ev_d is not None and ebitda_d is not None and ebitda_d > Decimal(0):
            ev_to_ebitda = to_float(ev_d / ebitda_d, round_digits=2)

        pe = None
        if eq_d is not None and ni_d is not None and ni_d > Decimal(0):
            pe = to_float(eq_d / ni_d, round_digits=2)

        return {
            "ev_to_revenue": ev_to_rev,
            "ev_to_ebitda": ev_to_ebitda,
            "pe_ratio": pe,
        }

    @staticmethod
    def calculate_statistics(values: List[float]) -> Dict[str, Optional[float]]:
        """Calculate min, 25th percentile, median, mean, 75th percentile, max across multiple values."""
        clean_vals = sorted([float(v) for v in values if v is not None and v > 0])
        if not clean_vals:
            return {
                "count": 0,
                "min": None,
                "percentile_25": None,
                "median": None,
                "mean": None,
                "percentile_75": None,
                "max": None,
            }

        n = len(clean_vals)
        mean_val = round(statistics.mean(clean_vals), 2)
        median_val = round(statistics.median(clean_vals), 2)
        min_val = round(min(clean_vals), 2)
        max_val = round(max(clean_vals), 2)

        p25 = round(clean_vals[int(0.25 * (n - 1))], 2)
        p75 = round(clean_vals[int(0.75 * (n - 1))], 2)

        return {
            "count": n,
            "min": min_val,
            "percentile_25": p25,
            "median": median_val,
            "mean": mean_val,
            "percentile_75": p75,
            "max": max_val,
        }

    @staticmethod
    def calculate_comp_cohort_statistics(companies: List[Dict[str, Any]], only_included: bool = True) -> Dict[str, Any]:
        """Compute statistical multiple benchmarks across active comparable companies."""
        filtered = [
            c for c in companies
            if not only_included or str(c.get("status", "INCLUDED")).upper() == "INCLUDED"
        ]

        ev_rev_vals = []
        ev_ebitda_vals = []
        pe_vals = []

        for comp in filtered:
            multiples = ComparableEngine.calculate_comp_multiples(comp)
            if multiples.get("ev_to_revenue") is not None:
                ev_rev_vals.append(multiples["ev_to_revenue"])
            if multiples.get("ev_to_ebitda") is not None:
                ev_ebitda_vals.append(multiples["ev_to_ebitda"])
            if multiples.get("pe_ratio") is not None:
                pe_vals.append(multiples["pe_ratio"])

        return {
            "total_companies": len(companies),
            "included_companies": len(filtered),
            "ev_to_revenue_stats": ComparableEngine.calculate_statistics(ev_rev_vals),
            "ev_to_ebitda_stats": ComparableEngine.calculate_statistics(ev_ebitda_vals),
            "pe_ratio_stats": ComparableEngine.calculate_statistics(pe_vals),
        }

    @staticmethod
    def calculate_implied_valuation(
        target_metric_value: Any,
        multiple_stats: Dict[str, Any],
        metric_type: str = "EBITDA",  # REVENUE or EBITDA
        cash: Any = 0.0,
        debt: Any = 0.0,
        minority_interest: Any = 0.0,
        preferred_equity: Any = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate Implied Enterprise Value and Equity Value Range based on target metric and benchmark multiples.
        """
        target_val_d = to_decimal(target_metric_value)
        if target_val_d is None or target_val_d <= Decimal(0):
            return {
                "metric_type": metric_type,
                "target_metric_value": None,
                "implied_enterprise_value_low": None,
                "implied_enterprise_value_base": None,
                "implied_enterprise_value_high": None,
                "implied_equity_value_base": None,
                "is_calculable": False,
            }

        min_mult = to_decimal(multiple_stats.get("percentile_25") or multiple_stats.get("min"))
        base_mult = to_decimal(multiple_stats.get("median") or multiple_stats.get("mean"))
        max_mult = to_decimal(multiple_stats.get("percentile_75") or multiple_stats.get("max"))

        if base_mult is None:
            return {
                "metric_type": metric_type,
                "target_metric_value": to_float(target_val_d),
                "implied_enterprise_value_low": None,
                "implied_enterprise_value_base": None,
                "implied_enterprise_value_high": None,
                "implied_equity_value_base": None,
                "is_calculable": False,
            }

        ev_low = target_val_d * min_mult if min_mult is not None else None
        ev_base = target_val_d * base_mult
        ev_high = target_val_d * max_mult if max_mult is not None else None

        bridge_low = ValuationBridgeEngine.bridge_enterprise_to_equity_value(
            ev_low, cash, debt, minority_interest, preferred_equity
        ) if ev_low else {}
        bridge_base = ValuationBridgeEngine.bridge_enterprise_to_equity_value(
            ev_base, cash, debt, minority_interest, preferred_equity
        )
        bridge_high = ValuationBridgeEngine.bridge_enterprise_to_equity_value(
            ev_high, cash, debt, minority_interest, preferred_equity
        ) if ev_high else {}

        return {
            "metric_type": metric_type,
            "target_metric_value": to_float(target_val_d),
            "multiple_low": to_float(min_mult),
            "multiple_base": to_float(base_mult),
            "multiple_high": to_float(max_mult),
            "implied_enterprise_value_low": to_float(ev_low),
            "implied_enterprise_value_base": to_float(ev_base),
            "implied_enterprise_value_high": to_float(ev_high),
            "implied_equity_value_low": bridge_low.get("equity_value"),
            "implied_equity_value_base": bridge_base.get("equity_value"),
            "implied_equity_value_high": bridge_high.get("equity_value"),
            "is_calculable": True,
        }
