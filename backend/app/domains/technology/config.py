"""30-Category Technology Diligence Taxonomy, Metric Types, and Lifecycle Enums."""

from enum import Enum
from typing import Dict, List, Optional, Set


class TechnologyCategory(str, Enum):
    """30-Category Technology & Product Diligence Taxonomy."""
    TECHNOLOGY_DEBT = "TECHNOLOGY_DEBT"
    LEGACY_ARCHITECTURE = "LEGACY_ARCHITECTURE"
    SCALABILITY = "SCALABILITY"
    CLOUD_INFRASTRUCTURE = "CLOUD_INFRASTRUCTURE"
    CLOUD_COST = "CLOUD_COST"
    API_DEPENDENCIES = "API_DEPENDENCIES"
    THIRD_PARTY_DEPENDENCIES = "THIRD_PARTY_DEPENDENCIES"
    VENDOR_LOCK_IN = "VENDOR_LOCK_IN"
    SINGLE_POINT_OF_FAILURE = "SINGLE_POINT_OF_FAILURE"
    DISASTER_RECOVERY = "DISASTER_RECOVERY"
    BACKUP_RECOVERY = "BACKUP_RECOVERY"
    BUSINESS_CONTINUITY = "BUSINESS_CONTINUITY"
    OBSERVABILITY = "OBSERVABILITY"
    SYSTEM_RELIABILITY = "SYSTEM_RELIABILITY"
    SLA_PERFORMANCE = "SLA_PERFORMANCE"
    INCIDENT_HISTORY = "INCIDENT_HISTORY"
    SECURITY_ARCHITECTURE = "SECURITY_ARCHITECTURE"
    VULNERABILITY_MANAGEMENT = "VULNERABILITY_MANAGEMENT"
    DEVOPS_MATURITY = "DEVOPS_MATURITY"
    CI_CD = "CI_CD"
    ENGINEERING_BANDWIDTH = "ENGINEERING_BANDWIDTH"
    KEY_ENGINEERING_PERSON_DEPENDENCY = "KEY_ENGINEERING_PERSON_DEPENDENCY"
    DOCUMENTATION_GAPS = "DOCUMENTATION_GAPS"
    DATA_ARCHITECTURE = "DATA_ARCHITECTURE"
    DATA_QUALITY = "DATA_QUALITY"
    INTEGRATION_COMPLEXITY = "INTEGRATION_COMPLEXITY"
    PRODUCT_ARCHITECTURE = "PRODUCT_ARCHITECTURE"
    PRODUCT_SCALABILITY = "PRODUCT_SCALABILITY"
    PRODUCT_TECHNICAL_RISK = "PRODUCT_TECHNICAL_RISK"
    ROADMAP_RISK = "ROADMAP_RISK"


class MetricCategory(str, Enum):
    """Operational KPI Classifications."""
    UPTIME_SLA = "UPTIME_SLA"
    INCIDENT_MTTR = "INCIDENT_MTTR"
    CLOUD_SPEND = "CLOUD_SPEND"
    BACKUP_RECOVERY = "BACKUP_RECOVERY"
    ENGINEERING_VELOCITY = "ENGINEERING_VELOCITY"
    SECURITY_VULNERABILITIES = "SECURITY_VULNERABILITIES"


class DependencyType(str, Enum):
    """External Technical Dependency Types."""
    CLOUD_PROVIDER = "CLOUD_PROVIDER"
    SAAS_API = "SAAS_API"
    DATABASE = "DATABASE"
    PAYMENT_GATEWAY = "PAYMENT_GATEWAY"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"


class TechFindingStatus(str, Enum):
    """Lifecycle stages for an identified technology finding."""
    IDENTIFIED = "IDENTIFIED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    REMEDIATION_PLANNED = "REMEDIATION_PLANNED"
    MITIGATED = "MITIGATED"
    ACCEPTED = "ACCEPTED"


VALID_TECH_TRANSITIONS: Dict[TechFindingStatus, Set[TechFindingStatus]] = {
    TechFindingStatus.IDENTIFIED: {
        TechFindingStatus.REQUIRES_REVIEW,
        TechFindingStatus.REMEDIATION_PLANNED,
        TechFindingStatus.ACCEPTED,
    },
    TechFindingStatus.REQUIRES_REVIEW: {
        TechFindingStatus.REMEDIATION_PLANNED,
        TechFindingStatus.MITIGATED,
        TechFindingStatus.ACCEPTED,
    },
    TechFindingStatus.REMEDIATION_PLANNED: {
        TechFindingStatus.MITIGATED,
        TechFindingStatus.REQUIRES_REVIEW,
    },
    TechFindingStatus.MITIGATED: {TechFindingStatus.REQUIRES_REVIEW},
    TechFindingStatus.ACCEPTED: {TechFindingStatus.REQUIRES_REVIEW},
}


def validate_tech_transition(current: str, target: str) -> None:
    """Enforce valid technology finding state transitions."""
    try:
        curr_enum = TechFindingStatus(current)
        target_enum = TechFindingStatus(target)
    except ValueError:
        raise ValueError(f"Invalid technology finding status. Current: '{current}', Target: '{target}'")

    if curr_enum == target_enum:
        return

    allowed = VALID_TECH_TRANSITIONS.get(curr_enum, set())
    if target_enum not in allowed:
        allowed_names = [s.value for s in allowed]
        raise ValueError(
            f"Illegal technology finding transition from '{curr_enum.value}' to '{target_enum.value}'. Allowed: {allowed_names}"
        )
