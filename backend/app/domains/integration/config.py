"""100-Day Integration Execution Taxonomy, Lifecycle State Machines, and Configurations."""

from enum import Enum
from typing import Dict, List, Optional, Set


class WorkstreamCategory(str, Enum):
    """17-Pillar Integration Workstream Taxonomy."""
    EXECUTIVE_GOVERNANCE = "EXECUTIVE_GOVERNANCE"
    FINANCE_ACCOUNTING = "FINANCE_ACCOUNTING"
    TECHNOLOGY_IT = "TECHNOLOGY_IT"
    DATA_SYSTEMS = "DATA_SYSTEMS"
    SALES = "SALES"
    MARKETING = "MARKETING"
    CUSTOMER_SUCCESS = "CUSTOMER_SUCCESS"
    PRODUCT = "PRODUCT"
    OPERATIONS = "OPERATIONS"
    PROCUREMENT = "PROCUREMENT"
    HUMAN_RESOURCES = "HUMAN_RESOURCES"
    LEGAL_COMPLIANCE = "LEGAL_COMPLIANCE"
    CYBERSECURITY = "CYBERSECURITY"
    ERP_CRM_INTEGRATION = "ERP_CRM_INTEGRATION"
    COMMUNICATIONS = "COMMUNICATIONS"
    SYNERGY_REALIZATION = "SYNERGY_REALIZATION"
    BUSINESS_CONTINUITY = "BUSINESS_CONTINUITY"


class WorkstreamStatus(str, Enum):
    """Workstream Lifecycle States."""
    NOT_STARTED = "NOT_STARTED"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    AT_RISK = "AT_RISK"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MilestoneStatus(str, Enum):
    """Milestone Lifecycle States."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    AT_RISK = "AT_RISK"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


class IntegrationPriority(str, Enum):
    """Execution Priority."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DependencyType(str, Enum):
    """Supported Predecessor/Successor Relationship Types."""
    FINISH_TO_START = "FINISH_TO_START"
    START_TO_START = "START_TO_START"
    FINISH_TO_FINISH = "FINISH_TO_FINISH"


class IntegrationHealthBand(str, Enum):
    """Deterministic Health Score Rating Bands."""
    HEALTHY = "HEALTHY"
    WATCH = "WATCH"
    AT_RISK = "AT_RISK"
    CRITICAL = "CRITICAL"


# Valid Workstream State Transitions
VALID_WORKSTREAM_TRANSITIONS: Dict[WorkstreamStatus, Set[WorkstreamStatus]] = {
    WorkstreamStatus.NOT_STARTED: {WorkstreamStatus.PLANNED, WorkstreamStatus.IN_PROGRESS, WorkstreamStatus.CANCELLED},
    WorkstreamStatus.PLANNED: {WorkstreamStatus.IN_PROGRESS, WorkstreamStatus.NOT_STARTED, WorkstreamStatus.CANCELLED},
    WorkstreamStatus.IN_PROGRESS: {
        WorkstreamStatus.AT_RISK,
        WorkstreamStatus.BLOCKED,
        WorkstreamStatus.COMPLETED,
        WorkstreamStatus.CANCELLED,
    },
    WorkstreamStatus.AT_RISK: {
        WorkstreamStatus.IN_PROGRESS,
        WorkstreamStatus.BLOCKED,
        WorkstreamStatus.COMPLETED,
        WorkstreamStatus.CANCELLED,
    },
    WorkstreamStatus.BLOCKED: {
        WorkstreamStatus.IN_PROGRESS,
        WorkstreamStatus.AT_RISK,
        WorkstreamStatus.CANCELLED,
    },
    WorkstreamStatus.COMPLETED: {WorkstreamStatus.IN_PROGRESS},
    WorkstreamStatus.CANCELLED: {WorkstreamStatus.NOT_STARTED},
}


def validate_workstream_transition(current: str, target: str) -> None:
    """Validate that moving from current status to target status obeys the state machine."""
    try:
        curr_enum = WorkstreamStatus(current)
        target_enum = WorkstreamStatus(target)
    except ValueError:
        raise ValueError(f"Invalid workstream status. Current: '{current}', Target: '{target}'")

    if curr_enum == target_enum:
        return

    allowed = VALID_WORKSTREAM_TRANSITIONS.get(curr_enum, set())
    if target_enum not in allowed:
        allowed_names = [s.value for s in allowed]
        raise ValueError(
            f"Illegal workstream transition from '{curr_enum.value}' to '{target_enum.value}'. Allowed: {allowed_names}"
        )


def get_100day_stage(target_day: int) -> str:
    """Determine 100-Day Program Stage for a given target day."""
    if target_day <= 0:
        return "DAY_0_CLOSE"
    elif target_day <= 30:
        return "DAYS_1_30_STABILIZE"
    elif target_day <= 60:
        return "DAYS_31_60_INTEGRATE"
    else:
        return "DAYS_61_100_OPTIMIZE"
