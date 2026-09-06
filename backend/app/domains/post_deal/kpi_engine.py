"""Authoritative Deterministic Financial & Operational KPI Engine for Post-Acquisition Intelligence.

All mathematical computations and financial calculations are strictly deterministic and isolated
outside of generative LLMs.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class ThesisStatus(str, Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    OFF_TRACK = "OFF_TRACK"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class PostDealKPIEngine:
    """Authoritative deterministic mathematical engine for post-acquisition performance."""

    @staticmethod
    def compute_revenue_growth_pct(
        actual_revenue: float, baseline_revenue: float
    ) -> Optional[float]:
        """Calculate revenue growth percentage vs baseline. Returns None if baseline is <= 0."""
        if baseline_revenue <= 0:
            return None
        growth = ((actual_revenue - baseline_revenue) / baseline_revenue) * 100.0
        return round(growth, 2)

    @staticmethod
    def compute_ebitda_margin_pct(
        ebitda: float, revenue: float
    ) -> Optional[float]:
        """Calculate EBITDA margin percentage. Returns None if revenue is <= 0."""
        if revenue <= 0:
            return None
        margin = (ebitda / revenue) * 100.0
        return round(margin, 2)

    @staticmethod
    def compute_synergy_realization_pct(
        realized_value: float, expected_value: float
    ) -> Optional[float]:
        """Calculate percentage of expected deal synergies realized. Returns None if expected <= 0."""
        if expected_value <= 0:
            return None
        pct = (realized_value / expected_value) * 100.0
        return round(pct, 2)

    @staticmethod
    def compute_integration_completion_pct(
        completed_milestones: int, total_milestones: int
    ) -> float:
        """Calculate 100-day integration milestone completion rate."""
        if total_milestones <= 0:
            return 0.0
        rate = (completed_milestones / total_milestones) * 100.0
        return round(min(100.0, max(0.0, rate)), 2)

    @staticmethod
    def compute_milestone_ontime_pct(
        ontime_milestones: int, total_milestones: int
    ) -> float:
        """Calculate on-time execution percentage for scheduled milestones."""
        if total_milestones <= 0:
            return 0.0
        rate = (ontime_milestones / total_milestones) * 100.0
        return round(min(100.0, max(0.0, rate)), 2)

    @staticmethod
    def compute_customer_retention_pct(
        retained_customers: int, starting_customers: int
    ) -> Optional[float]:
        """Calculate logo / account retention rate."""
        if starting_customers <= 0:
            return None
        rate = (retained_customers / starting_customers) * 100.0
        return round(min(100.0, max(0.0, rate)), 2)

    @staticmethod
    def compute_net_revenue_retention_pct(
        starting_arr: float,
        expansion_arr: float = 0.0,
        churned_arr: float = 0.0,
        contraction_arr: float = 0.0,
    ) -> Optional[float]:
        """
        Calculate Net Revenue Retention (NRR):
        NRR = ((Starting ARR + Expansion ARR - Churned ARR - Contraction ARR) / Starting ARR) * 100%
        """
        if starting_arr <= 0:
            return None
        ending_arr = starting_arr + expansion_arr - churned_arr - contraction_arr
        nrr = (ending_arr / starting_arr) * 100.0
        return round(nrr, 2)

    @staticmethod
    def compute_churn_rate_pct(
        churned_amount: float, total_amount: float
    ) -> Optional[float]:
        """Calculate churn rate percentage (either ARR or customer count based)."""
        if total_amount <= 0:
            return None
        rate = (churned_amount / total_amount) * 100.0
        return round(min(100.0, max(0.0, rate)), 2)

    @staticmethod
    def compute_cost_savings_pct(
        realized_savings: float, baseline_operating_cost: float
    ) -> Optional[float]:
        """Calculate cost savings realized as a percentage of baseline operating costs."""
        if baseline_operating_cost <= 0:
            return None
        pct = (realized_savings / baseline_operating_cost) * 100.0
        return round(pct, 2)

    @staticmethod
    def evaluate_thesis_pillar_status(
        actual_value: Optional[float],
        target_value: float,
        is_higher_better: bool = True,
        tolerance_pct: float = 10.0,
    ) -> ThesisStatus:
        """
        Authoritative deterministic classification of Acquisition Thesis status:
        - ON_TRACK
        - AT_RISK
        - OFF_TRACK
        - INSUFFICIENT_DATA
        """
        if actual_value is None:
            return ThesisStatus.INSUFFICIENT_DATA
        if target_value == 0:
            return ThesisStatus.INSUFFICIENT_DATA

        if is_higher_better:
            variance_pct = ((actual_value - target_value) / abs(target_value)) * 100.0
            if variance_pct >= -tolerance_pct:
                return ThesisStatus.ON_TRACK
            elif variance_pct >= -2.0 * tolerance_pct:
                return ThesisStatus.AT_RISK
            else:
                return ThesisStatus.OFF_TRACK
        else:
            # Lower is better (e.g. churn rate, cloud spend, blocker count)
            variance_pct = ((actual_value - target_value) / abs(target_value)) * 100.0
            if variance_pct <= tolerance_pct:
                return ThesisStatus.ON_TRACK
            elif variance_pct <= 2.0 * tolerance_pct:
                return ThesisStatus.AT_RISK
            else:
                return ThesisStatus.OFF_TRACK

    @classmethod
    def compute_executive_value_creation_summary(
        cls,
        revenue_actual: Optional[float],
        revenue_target: Optional[float],
        ebitda_actual: Optional[float],
        ebitda_target: Optional[float],
        synergy_realized: float,
        synergy_expected: float,
        integration_completion_pct: float,
        open_blockers_count: int,
        customer_nrr_pct: Optional[float],
    ) -> Dict[str, Any]:
        """Synthesize overall value creation score and thesis tracking summary."""
        pillars = {}

        # 1. Revenue Pillar
        if revenue_actual is not None and revenue_target is not None and revenue_target > 0:
            pillars["revenue"] = {
                "actual": revenue_actual,
                "target": revenue_target,
                "variance_pct": round(((revenue_actual - revenue_target) / revenue_target) * 100.0, 2),
                "status": cls.evaluate_thesis_pillar_status(revenue_actual, revenue_target, is_higher_better=True).value,
            }
        else:
            pillars["revenue"] = {"status": ThesisStatus.INSUFFICIENT_DATA.value}

        # 2. EBITDA Pillar
        if ebitda_actual is not None and ebitda_target is not None and ebitda_target > 0:
            pillars["ebitda"] = {
                "actual": ebitda_actual,
                "target": ebitda_target,
                "variance_pct": round(((ebitda_actual - ebitda_target) / ebitda_target) * 100.0, 2),
                "status": cls.evaluate_thesis_pillar_status(ebitda_actual, ebitda_target, is_higher_better=True).value,
            }
        else:
            pillars["ebitda"] = {"status": ThesisStatus.INSUFFICIENT_DATA.value}

        # 3. Synergy Pillar
        if synergy_expected > 0:
            syn_pct = cls.compute_synergy_realization_pct(synergy_realized, synergy_expected)
            pillars["synergies"] = {
                "realized": synergy_realized,
                "expected": synergy_expected,
                "realization_pct": syn_pct,
                "status": cls.evaluate_thesis_pillar_status(synergy_realized, synergy_expected, is_higher_better=True).value,
            }
        else:
            pillars["synergies"] = {"status": ThesisStatus.INSUFFICIENT_DATA.value}

        # 4. Integration Pillar
        integration_status = ThesisStatus.ON_TRACK
        if open_blockers_count > 2 or integration_completion_pct < 40.0:
            integration_status = ThesisStatus.AT_RISK if open_blockers_count <= 4 else ThesisStatus.OFF_TRACK
        pillars["integration"] = {
            "completion_pct": integration_completion_pct,
            "open_blockers": open_blockers_count,
            "status": integration_status.value,
        }

        # 5. Customer Pillar
        if customer_nrr_pct is not None:
            pillars["customer"] = {
                "nrr_pct": customer_nrr_pct,
                "status": cls.evaluate_thesis_pillar_status(customer_nrr_pct, 100.0, is_higher_better=True).value,
            }
        else:
            pillars["customer"] = {"status": ThesisStatus.INSUFFICIENT_DATA.value}

        # Overall Status Synthesis
        statuses = [p["status"] for p in pillars.values() if p.get("status") != ThesisStatus.INSUFFICIENT_DATA.value]
        if not statuses:
            overall_status = ThesisStatus.INSUFFICIENT_DATA.value
        elif ThesisStatus.OFF_TRACK.value in statuses:
            overall_status = ThesisStatus.OFF_TRACK.value
        elif ThesisStatus.AT_RISK.value in statuses:
            overall_status = ThesisStatus.AT_RISK.value
        else:
            overall_status = ThesisStatus.ON_TRACK.value

        return {
            "overall_status": overall_status,
            "pillars": pillars,
        }
