"""Enterprise Value to Equity Value Bridge & Transaction Comparison Engine."""

from decimal import Decimal
from typing import Any, Dict, Optional
from app.domains.financials.engine.statements import to_decimal, to_float


class ValuationBridgeEngine:
    """Computes exact bridges between Enterprise Value and Equity Value, and transaction premium/discount."""

    @staticmethod
    def bridge_enterprise_to_equity_value(
        enterprise_value: Any,
        cash: Any = 0.0,
        debt: Any = 0.0,
        minority_interest: Any = 0.0,
        preferred_equity: Any = 0.0,
        pension_liabilities: Any = 0.0,
        other_adjustments: Any = 0.0,
    ) -> Dict[str, Any]:
        """
        Equity Value = Enterprise Value + Cash - Debt - Minority Interest - Preferred Equity - Pension Liabilities +/- Adjustments
        """
        ev_d = to_decimal(enterprise_value)
        if ev_d is None:
            return {
                "enterprise_value": None,
                "cash": to_float(to_decimal(cash)),
                "debt": to_float(to_decimal(debt)),
                "equity_value": None,
                "missing_inputs": ["enterprise_value"],
                "is_calculable": False,
            }

        c_d = to_decimal(cash) or Decimal(0)
        d_d = to_decimal(debt) or Decimal(0)
        mi_d = to_decimal(minority_interest) or Decimal(0)
        pe_d = to_decimal(preferred_equity) or Decimal(0)
        pl_d = to_decimal(pension_liabilities) or Decimal(0)
        adj_d = to_decimal(other_adjustments) or Decimal(0)

        # Net Debt = Debt - Cash
        net_debt = d_d - c_d

        # Equity Value = EV - Net Debt - Other claims
        equity_val = ev_d + c_d - d_d - mi_d - pe_d - pl_d + adj_d

        return {
            "enterprise_value": to_float(ev_d),
            "cash_and_equivalents": to_float(c_d),
            "total_debt": to_float(d_d),
            "net_debt": to_float(net_debt),
            "minority_interest": to_float(mi_d),
            "preferred_equity": to_float(pe_d),
            "pension_liabilities": to_float(pl_d),
            "other_adjustments": to_float(adj_d),
            "equity_value": to_float(equity_val),
            "formula": "Equity Value = EV + Cash - Debt - Minority Int - Preferred Eq - Pension + Adjustments",
            "is_calculable": True,
        }

    @staticmethod
    def calculate_transaction_comparison(
        proposed_ev: Any,
        proposed_equity_value: Any,
        benchmark_ev: Any,
        revenue: Any = None,
        ebitda: Any = None,
    ) -> Dict[str, Any]:
        """
        Calculate implied multiples and premium / discount % of proposed transaction price vs benchmark.
        """
        prop_ev_d = to_decimal(proposed_ev)
        bench_ev_d = to_decimal(benchmark_ev)
        rev_d = to_decimal(revenue)
        ebitda_d = to_decimal(ebitda)

        premium_pct = None
        if prop_ev_d is not None and bench_ev_d is not None and bench_ev_d > Decimal(0):
            diff = prop_ev_d - bench_ev_d
            premium_pct = to_float((diff / bench_ev_d) * Decimal(100), round_digits=2)

        implied_ev_to_rev = None
        if prop_ev_d is not None and rev_d is not None and rev_d > Decimal(0):
            implied_ev_to_rev = to_float(prop_ev_d / rev_d, round_digits=2)

        implied_ev_to_ebitda = None
        if prop_ev_d is not None and ebitda_d is not None and ebitda_d > Decimal(0):
            implied_ev_to_ebitda = to_float(prop_ev_d / ebitda_d, round_digits=2)

        return {
            "proposed_enterprise_value": to_float(prop_ev_d),
            "proposed_equity_value": to_float(to_decimal(proposed_equity_value)),
            "benchmark_enterprise_value": to_float(bench_ev_d),
            "premium_discount_pct": premium_pct,
            "implied_ev_to_revenue": implied_ev_to_rev,
            "implied_ev_to_ebitda": implied_ev_to_ebitda,
        }
