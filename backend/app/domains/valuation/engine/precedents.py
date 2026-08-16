"""Precedent Transactions Analysis (PTA) Calculation Engine."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.domains.financials.engine.statements import to_decimal, to_float
from app.domains.valuation.engine.bridge import ValuationBridgeEngine
from app.domains.valuation.engine.comparables import ComparableEngine


class PrecedentEngine:
    """Computes M&A precedent deal multiples, transaction percentiles, and implied EV/Equity values."""

    @staticmethod
    def calculate_deal_multiples(deal: Dict[str, Any]) -> Dict[str, Any]:
        """Derive EV/Revenue and EV/EBITDA multiples for an individual historical M&A deal."""
        ev_d = to_decimal(deal.get("enterprise_value") or deal.get("transaction_value"))
        rev_d = to_decimal(deal.get("revenue"))
        ebitda_d = to_decimal(deal.get("ebitda"))

        ev_to_rev = None
        if ev_d is not None and rev_d is not None and rev_d > Decimal(0):
            ev_to_rev = to_float(ev_d / rev_d, round_digits=2)

        ev_to_ebitda = None
        if ev_d is not None and ebitda_d is not None and ebitda_d > Decimal(0):
            ev_to_ebitda = to_float(ev_d / ebitda_d, round_digits=2)

        return {
            "ev_to_revenue": ev_to_rev,
            "ev_to_ebitda": ev_to_ebitda,
        }

    @staticmethod
    def calculate_precedent_cohort_statistics(
        transactions: List[Dict[str, Any]], only_included: bool = True
    ) -> Dict[str, Any]:
        """Compute statistical multiple benchmarks across historical M&A transactions."""
        filtered = [
            t for t in transactions
            if not only_included or str(t.get("status", "INCLUDED")).upper() == "INCLUDED"
        ]

        ev_rev_vals = []
        ev_ebitda_vals = []

        for tx in filtered:
            multiples = PrecedentEngine.calculate_deal_multiples(tx)
            if multiples.get("ev_to_revenue") is not None:
                ev_rev_vals.append(multiples["ev_to_revenue"])
            if multiples.get("ev_to_ebitda") is not None:
                ev_ebitda_vals.append(multiples["ev_to_ebitda"])

        return {
            "total_transactions": len(transactions),
            "included_transactions": len(filtered),
            "ev_to_revenue_stats": ComparableEngine.calculate_statistics(ev_rev_vals),
            "ev_to_ebitda_stats": ComparableEngine.calculate_statistics(ev_ebitda_vals),
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
        """Calculate Implied Valuation Range from Precedent Transaction Multiples."""
        return ComparableEngine.calculate_implied_valuation(
            target_metric_value=target_metric_value,
            multiple_stats=multiple_stats,
            metric_type=metric_type,
            cash=cash,
            debt=debt,
            minority_interest=minority_interest,
            preferred_equity=preferred_equity,
        )
