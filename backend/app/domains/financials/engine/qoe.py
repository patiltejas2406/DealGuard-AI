"""Quality of Earnings (QoE) EBITDA Normalization Bridge Engine."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from app.domains.financials.engine.statements import to_decimal, to_float


class QoEEngine:
    """Computes transparent, auditable EBITDA Quality of Earnings normalization bridges."""

    @staticmethod
    def calculate_adjusted_ebitda(
        reported_ebitda: Any,
        adjustments: List[Dict[str, Any]],
        only_approved: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate Adjusted EBITDA Bridge:
        Adjusted EBITDA = Reported EBITDA + Add-Backs - Deductions.
        """
        ebitda_d = to_decimal(reported_ebitda)
        if ebitda_d is None:
            return {
                "reported_ebitda": None,
                "total_add_backs": 0.0,
                "total_deductions": 0.0,
                "net_adjustment": 0.0,
                "adjusted_ebitda": None,
                "adjustment_count": len(adjustments),
                "category_breakdown": {},
            }

        total_add_backs = Decimal(0)
        total_deductions = Decimal(0)
        category_breakdown: Dict[str, float] = {}

        for adj in adjustments:
            status = str(adj.get("status", "PROPOSED")).upper()
            if only_approved and status != "APPROVED":
                continue

            amount_d = to_decimal(adj.get("amount", 0)) or Decimal(0)
            treatment = str(adj.get("treatment", "ADD_BACK")).upper()
            category = str(adj.get("category", "OTHER")).upper()

            if treatment == "ADD_BACK":
                total_add_backs += amount_d
                category_breakdown[category] = category_breakdown.get(category, 0.0) + float(amount_d)
            elif treatment == "DEDUCTION":
                total_deductions += amount_d
                category_breakdown[category] = category_breakdown.get(category, 0.0) - float(amount_d)

        net_adj = total_add_backs - total_deductions
        adjusted_ebitda = ebitda_d + net_adj

        return {
            "reported_ebitda": to_float(ebitda_d),
            "total_add_backs": to_float(total_add_backs),
            "total_deductions": to_float(total_deductions),
            "net_adjustment": to_float(net_adj),
            "adjusted_ebitda": to_float(adjusted_ebitda),
            "adjustment_count": len(adjustments),
            "applied_adjustments_count": len(
                [a for a in adjustments if (not only_approved or str(a.get("status", "")).upper() == "APPROVED")]
            ),
            "category_breakdown": {k: round(v, 2) for k, v in category_breakdown.items()},
        }
