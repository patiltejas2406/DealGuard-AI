"""Centralized Taxonomy, Lifecycle State Machine, and Mathematical Configuration for Synergy Engine."""

from enum import Enum
from typing import Any, Dict, List, Optional, Set


class SynergyType(str, Enum):
    """Broad synergy classifications."""
    REVENUE = "REVENUE"
    COST = "COST"
    OPERATIONAL = "OPERATIONAL"


class SynergyCategory(str, Enum):
    """Detailed category taxonomy for revenue, cost, and operational synergies."""
    # Revenue Synergies
    CROSS_SELLING = "CROSS_SELLING"
    UPSELLING = "UPSELLING"
    PRICING = "PRICING"
    CUSTOMER_RETENTION = "CUSTOMER_RETENTION"
    GEOGRAPHIC_EXPANSION = "GEOGRAPHIC_EXPANSION"
    PRODUCT_BUNDLING = "PRODUCT_BUNDLING"
    CHANNEL_EXPANSION = "CHANNEL_EXPANSION"

    # Cost Synergies
    PROCUREMENT = "PROCUREMENT"
    HEADCOUNT = "HEADCOUNT"
    TECHNOLOGY = "TECHNOLOGY"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    FACILITIES = "FACILITIES"
    VENDOR_CONSOLIDATION = "VENDOR_CONSOLIDATION"
    SHARED_SERVICES = "SHARED_SERVICES"
    PROCESS_AUTOMATION = "PROCESS_AUTOMATION"

    # Operational Synergies
    WORKING_CAPITAL = "WORKING_CAPITAL"
    CAPEX_OPTIMIZATION = "CAPEX_OPTIMIZATION"
    PROCESS_EFFICIENCY = "PROCESS_EFFICIENCY"


class SynergyStatus(str, Enum):
    """Lifecycle stages of a value creation opportunity."""
    IDENTIFIED = "IDENTIFIED"
    VALIDATED = "VALIDATED"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    PARTIALLY_REALIZED = "PARTIALLY_REALIZED"
    REALIZED = "REALIZED"
    AT_RISK = "AT_RISK"
    ABANDONED = "ABANDONED"


class SynergyConfidence(str, Enum):
    """Evidence and analytical backing confidence level."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Valid State Transitions in Synergy Lifecycle
VALID_STATUS_TRANSITIONS: Dict[SynergyStatus, Set[SynergyStatus]] = {
    SynergyStatus.IDENTIFIED: {SynergyStatus.VALIDATED, SynergyStatus.ABANDONED},
    SynergyStatus.VALIDATED: {SynergyStatus.PLANNED, SynergyStatus.IDENTIFIED, SynergyStatus.ABANDONED},
    SynergyStatus.PLANNED: {SynergyStatus.IN_PROGRESS, SynergyStatus.VALIDATED, SynergyStatus.ABANDONED},
    SynergyStatus.IN_PROGRESS: {
        SynergyStatus.PARTIALLY_REALIZED,
        SynergyStatus.REALIZED,
        SynergyStatus.AT_RISK,
        SynergyStatus.ABANDONED,
    },
    SynergyStatus.PARTIALLY_REALIZED: {
        SynergyStatus.REALIZED,
        SynergyStatus.AT_RISK,
        SynergyStatus.IN_PROGRESS,
        SynergyStatus.ABANDONED,
    },
    SynergyStatus.AT_RISK: {
        SynergyStatus.IN_PROGRESS,
        SynergyStatus.PARTIALLY_REALIZED,
        SynergyStatus.REALIZED,
        SynergyStatus.ABANDONED,
    },
    SynergyStatus.REALIZED: {SynergyStatus.PARTIALLY_REALIZED},
    SynergyStatus.ABANDONED: {SynergyStatus.IDENTIFIED},
}


def validate_status_transition(current: str, target: str) -> None:
    """Validate that moving from current status to target status obeys the state machine."""
    try:
        curr_enum = SynergyStatus(current)
        target_enum = SynergyStatus(target)
    except ValueError:
        raise ValueError(f"Invalid status value. Current: '{current}', Target: '{target}'")

    if curr_enum == target_enum:
        return

    allowed = VALID_STATUS_TRANSITIONS.get(curr_enum, set())
    if target_enum not in allowed:
        allowed_names = [s.value for s in allowed]
        raise ValueError(
            f"Illegal status transition from '{curr_enum.value}' to '{target_enum.value}'. Allowed transitions: {allowed_names}"
        )


# Default 5-Year Realization Curves (%)
DEFAULT_REALIZATION_CURVES: Dict[str, Dict[str, float]] = {
    "STANDARD": {"year_1": 20.0, "year_2": 50.0, "year_3": 80.0, "year_4": 100.0, "year_5": 100.0},
    "AGGRESSIVE": {"year_1": 50.0, "year_2": 85.0, "year_3": 100.0, "year_4": 100.0, "year_5": 100.0},
    "CONSERVATIVE": {"year_1": 10.0, "year_2": 30.0, "year_3": 60.0, "year_4": 85.0, "year_5": 100.0},
    "IMMEDIATE": {"year_1": 100.0, "year_2": 100.0, "year_3": 100.0, "year_4": 100.0, "year_5": 100.0},
}


def calculate_potential_value(baseline: float, target: float, synergy_type: str) -> float:
    """Compute potential annual value: for cost savings |baseline - target|, for revenue max(0, target - baseline)."""
    if synergy_type == SynergyType.COST.value:
        return max(0.0, float(baseline) - float(target)) if baseline > 0 else max(0.0, float(target))
    else:
        return max(0.0, float(target) - float(baseline)) if baseline > 0 else max(0.0, float(target))


def calculate_expected_value(potential: float, realization_rate_pct: float, probability_pct: float) -> float:
    """Expected annual value = Potential * (Realization % / 100) * (Probability % / 100)."""
    r_rate = max(0.0, min(100.0, float(realization_rate_pct))) / 100.0
    p_rate = max(0.0, min(100.0, float(probability_pct))) / 100.0
    return round(float(potential) * r_rate * p_rate, 2)


def calculate_value_capture_rate(realized: float, planned_or_potential: float) -> float:
    """Value Capture Rate (%) = Realized / Potential * 100."""
    if planned_or_potential <= 0.0:
        return 0.0
    return round((float(realized) / float(planned_or_potential)) * 100.0, 1)
