"""Deterministic Discounted Cash Flow (DCF) & Unlevered Free Cash Flow (UFCF) Engine."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from app.core.exceptions import ValidationException
from app.domains.financials.engine.statements import to_decimal, to_float
from app.domains.valuation.engine.bridge import ValuationBridgeEngine


class DCFEngine:
    """Computes exact, auditable Discounted Cash Flow valuations and cash flow schedules."""

    @staticmethod
    def calculate_ufcf(
        ebit: Any,
        tax_rate: Any,
        depreciation_amortization: Any,
        capex: Any,
        working_capital_change: Any,
    ) -> Dict[str, Any]:
        """
        Unlevered Free Cash Flow (UFCF) = EBIT * (1 - Tax Rate) + D&A - CapEx - Delta Working Capital
        """
        ebit_d = to_decimal(ebit)
        tax_d = to_decimal(tax_rate)
        dna_d = to_decimal(depreciation_amortization)
        capex_d = to_decimal(capex)
        wc_d = to_decimal(working_capital_change)

        missing = []
        if ebit_d is None:
            missing.append("ebit")
        if tax_d is None:
            missing.append("tax_rate")
        if dna_d is None:
            missing.append("depreciation_amortization")
        if capex_d is None:
            missing.append("capex")
        if wc_d is None:
            missing.append("working_capital_change")

        if missing:
            return {
                "ufcf": None,
                "nopat": None,
                "missing_inputs": missing,
                "is_calculable": False,
            }

        # Normalize tax rate
        tax_ratio = tax_d / Decimal(100) if tax_d > Decimal(1) else tax_d

        # NOPAT = EBIT * (1 - t)
        nopat = ebit_d * (Decimal(1) - tax_ratio)

        # UFCF = NOPAT + D&A - CapEx - Delta WC
        ufcf = nopat + dna_d - abs(capex_d) - wc_d

        return {
            "ebit": to_float(ebit_d),
            "tax_rate_pct": to_float(tax_ratio * Decimal(100)),
            "nopat": to_float(nopat),
            "depreciation_amortization": to_float(dna_d),
            "capex": to_float(abs(capex_d)),
            "working_capital_change": to_float(wc_d),
            "ufcf": to_float(ufcf),
            "formula": "UFCF = EBIT × (1 - Tax Rate) + D&A - CapEx - ΔWC",
            "is_calculable": True,
        }

    @staticmethod
    def calculate_dcf(
        projections: List[Dict[str, Any]],
        wacc: Any,
        terminal_growth_rate: Any = 3.0,
        exit_multiple: Any = 10.0,
        terminal_method: str = "PERPETUITY_GROWTH",  # PERPETUITY_GROWTH or EXIT_MULTIPLE
        cash: Any = 0.0,
        debt: Any = 0.0,
        minority_interest: Any = 0.0,
        preferred_equity: Any = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate complete multi-period DCF schedule, Terminal Value, EV, and Equity Value Bridge.
        """
        wacc_d = to_decimal(wacc)
        if wacc_d is None or wacc_d <= Decimal(0):
            raise ValidationException("WACC must be a positive number greater than 0.")

        wacc_ratio = wacc_d / Decimal(100) if wacc_d > Decimal(1) else wacc_d
        g_d = to_decimal(terminal_growth_rate) or Decimal(3)
        g_ratio = g_d / Decimal(100) if g_d > Decimal(1) else g_d
        exit_mult_d = to_decimal(exit_multiple) or Decimal(10)

        terminal_method_clean = terminal_method.upper()
        if terminal_method_clean == "PERPETUITY_GROWTH":
            if wacc_ratio <= g_ratio:
                raise ValidationException(
                    f"WACC ({float(wacc_ratio*100):.2f}%) must be strictly greater than terminal growth rate ({float(g_ratio*100):.2f}%)."
                )

        if not projections:
            raise ValidationException("At least one projection period is required for DCF calculation.")

        schedule: List[Dict[str, Any]] = []
        pv_fcf_sum = Decimal(0)

        for idx, p in enumerate(projections, start=1):
            period_label = p.get("period", f"Year {idx}")
            ebit = to_decimal(p.get("ebit"))
            tax_rate = to_decimal(p.get("tax_rate", 25.0))
            dna = to_decimal(p.get("depreciation_amortization", 0.0))
            capex = to_decimal(p.get("capex", 0.0))
            wc_change = to_decimal(p.get("working_capital_change", 0.0))

            ufcf_res = DCFEngine.calculate_ufcf(ebit, tax_rate, dna, capex, wc_change)
            ufcf_val = to_decimal(ufcf_res.get("ufcf")) or Decimal(0)

            # Discount Factor = 1 / (1 + WACC)^t
            discount_factor = Decimal(1) / ((Decimal(1) + wacc_ratio) ** Decimal(idx))
            pv_ufcf = ufcf_val * discount_factor
            pv_fcf_sum += pv_ufcf

            schedule.append({
                "period": period_label,
                "year_index": idx,
                "revenue": to_float(to_decimal(p.get("revenue"))),
                "revenue_growth": to_float(to_decimal(p.get("revenue_growth"))),
                "ebitda": to_float(to_decimal(p.get("ebitda"))),
                "ebitda_margin": to_float(to_decimal(p.get("ebitda_margin"))),
                "ebit": to_float(ebit),
                "tax_rate": to_float(tax_rate),
                "nopat": ufcf_res.get("nopat"),
                "depreciation_amortization": to_float(dna),
                "capex": to_float(capex),
                "working_capital_change": to_float(wc_change),
                "ufcf": to_float(ufcf_val),
                "discount_factor": to_float(discount_factor, round_digits=4),
                "pv_ufcf": to_float(pv_ufcf),
            })

        final_period = projections[-1]
        final_ufcf = to_decimal(schedule[-1]["ufcf"]) or Decimal(0)
        final_ebitda = to_decimal(final_period.get("ebitda")) or (to_decimal(final_period.get("ebit", 0)) + to_decimal(final_period.get("depreciation_amortization", 0)))
        final_year_idx = len(projections)
        final_discount_factor = Decimal(1) / ((Decimal(1) + wacc_ratio) ** Decimal(final_year_idx))

        # Terminal Value Calculation
        if terminal_method_clean == "PERPETUITY_GROWTH":
            # TV = Final UFCF * (1 + g) / (WACC - g)
            terminal_value = (final_ufcf * (Decimal(1) + g_ratio)) / (wacc_ratio - g_ratio)
            tv_formula = f"TV = ({to_float(final_ufcf)} × (1 + {to_float(g_ratio*100)}%)) / ({to_float(wacc_ratio*100)}% - {to_float(g_ratio*100)}%)"
        else:
            # Exit Multiple: TV = Final EBITDA * Multiple
            terminal_value = final_ebitda * exit_mult_d
            tv_formula = f"TV = Final EBITDA ({to_float(final_ebitda)}) × Exit Multiple ({to_float(exit_mult_d)}x)"

        pv_terminal_value = terminal_value * final_discount_factor
        implied_enterprise_value = pv_fcf_sum + pv_terminal_value

        # EV to Equity Value Bridge
        bridge_res = ValuationBridgeEngine.bridge_enterprise_to_equity_value(
            enterprise_value=implied_enterprise_value,
            cash=cash,
            debt=debt,
            minority_interest=minority_interest,
            preferred_equity=preferred_equity,
        )

        return {
            "terminal_method": terminal_method_clean,
            "wacc_pct": to_float(wacc_ratio * Decimal(100)),
            "terminal_growth_rate_pct": to_float(g_ratio * Decimal(100)) if terminal_method_clean == "PERPETUITY_GROWTH" else None,
            "exit_multiple": to_float(exit_mult_d) if terminal_method_clean == "EXIT_MULTIPLE" else None,
            "pv_forecast_fcf": to_float(pv_fcf_sum),
            "terminal_value": to_float(terminal_value),
            "pv_terminal_value": to_float(pv_terminal_value),
            "terminal_value_formula": tv_formula,
            "implied_enterprise_value": to_float(implied_enterprise_value),
            "implied_equity_value": bridge_res.get("equity_value"),
            "schedule": schedule,
            "bridge": bridge_res,
        }
