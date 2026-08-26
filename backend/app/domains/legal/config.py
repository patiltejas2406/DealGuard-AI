"""32-Category Legal & Contract Taxonomy, Compliance Frameworks, and Status State Machines."""

from enum import Enum
from typing import Dict, List, Optional, Set


class ContractCategory(str, Enum):
    """32-Category Contract & Clause Taxonomy."""
    CHANGE_OF_CONTROL = "CHANGE_OF_CONTROL"
    ASSIGNMENT_RESTRICTION = "ASSIGNMENT_RESTRICTION"
    TERMINATION_RIGHT = "TERMINATION_RIGHT"
    CONSENT_REQUIREMENT = "CONSENT_REQUIREMENT"
    NON_COMPETE = "NON_COMPETE"
    NON_SOLICITATION = "NON_SOLICITATION"
    IP_OWNERSHIP = "IP_OWNERSHIP"
    IP_ASSIGNMENT = "IP_ASSIGNMENT"
    LICENSE_RESTRICTION = "LICENSE_RESTRICTION"
    EXCLUSIVITY = "EXCLUSIVITY"
    AUTO_RENEWAL = "AUTO_RENEWAL"
    TERMINATION_NOTICE = "TERMINATION_NOTICE"
    LIABILITY_CAP = "LIABILITY_CAP"
    INDEMNIFICATION = "INDEMNIFICATION"
    WARRANTY = "WARRANTY"
    REPRESENTATION = "REPRESENTATION"
    GOVERNING_LAW = "GOVERNING_LAW"
    JURISDICTION = "JURISDICTION"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    DATA_PRIVACY = "DATA_PRIVACY"
    DATA_PROCESSING = "DATA_PROCESSING"
    REGULATORY_OBLIGATION = "REGULATORY_OBLIGATION"
    COMPLIANCE_OBLIGATION = "COMPLIANCE_OBLIGATION"
    INSURANCE_REQUIREMENT = "INSURANCE_REQUIREMENT"
    PAYMENT_TERMS = "PAYMENT_TERMS"
    PRICE_ESCALATION = "PRICE_ESCALATION"
    MOST_FAVORED_CUSTOMER = "MOST_FAVORED_CUSTOMER"
    AUDIT_RIGHT = "AUDIT_RIGHT"
    SUBCONTRACTING = "SUBCONTRACTING"
    SERVICE_LEVEL = "SERVICE_LEVEL"
    MATERIAL_ADVERSE_EFFECT = "MATERIAL_ADVERSE_EFFECT"
    LITIGATION_REFERENCE = "LITIGATION_REFERENCE"


class ContractType(str, Enum):
    """Broad Agreement Classifications."""
    CUSTOMER_MSA = "CUSTOMER_MSA"
    VENDOR_SAAS = "VENDOR_SAAS"
    EMPLOYMENT = "EMPLOYMENT"
    IP_ASSIGNMENT = "IP_ASSIGNMENT"
    PARTNERSHIP = "PARTNERSHIP"
    LEASE = "LEASE"
    CREDIT_AGREEMENT = "CREDIT_AGREEMENT"
    NDA = "NDA"
    DISTRIBUTION = "DISTRIBUTION"
    DATA_PROCESSING_AGREEMENT = "DATA_PROCESSING_AGREEMENT"
    INSURANCE_POLICY = "INSURANCE_POLICY"


class ComplianceFramework(str, Enum):
    """Supported Compliance Frameworks."""
    GDPR = "GDPR"
    CCPA = "CCPA"
    SOC2 = "SOC2"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI_DSS"
    REGULATORY_LICENSES = "REGULATORY_LICENSES"
    EMPLOYMENT_LABOR = "EMPLOYMENT_LABOR"
    CYBERSECURITY = "CYBERSECURITY"
    INSURANCE = "INSURANCE"


class LegalFindingStatus(str, Enum):
    """Lifecycle stages for an identified legal exposure."""
    IDENTIFIED = "IDENTIFIED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    ACTION_PLANNED = "ACTION_PLANNED"
    CONSENT_OBTAINED = "CONSENT_OBTAINED"
    MITIGATED = "MITIGATED"
    ACCEPTED = "ACCEPTED"


class ComplianceStatus(str, Enum):
    """Evidence status for a compliance requirement."""
    EVIDENCE_PRESENT = "EVIDENCE_PRESENT"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    POTENTIAL_GAP = "POTENTIAL_GAP"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    COMPLIANT = "COMPLIANT"


VALID_FINDING_TRANSITIONS: Dict[LegalFindingStatus, Set[LegalFindingStatus]] = {
    LegalFindingStatus.IDENTIFIED: {
        LegalFindingStatus.REQUIRES_REVIEW,
        LegalFindingStatus.ACTION_PLANNED,
        LegalFindingStatus.ACCEPTED,
    },
    LegalFindingStatus.REQUIRES_REVIEW: {
        LegalFindingStatus.ACTION_PLANNED,
        LegalFindingStatus.MITIGATED,
        LegalFindingStatus.ACCEPTED,
    },
    LegalFindingStatus.ACTION_PLANNED: {
        LegalFindingStatus.CONSENT_OBTAINED,
        LegalFindingStatus.MITIGATED,
        LegalFindingStatus.REQUIRES_REVIEW,
    },
    LegalFindingStatus.CONSENT_OBTAINED: {LegalFindingStatus.MITIGATED},
    LegalFindingStatus.MITIGATED: {LegalFindingStatus.REQUIRES_REVIEW},
    LegalFindingStatus.ACCEPTED: {LegalFindingStatus.REQUIRES_REVIEW},
}


def validate_finding_transition(current: str, target: str) -> None:
    """Enforce valid legal finding state machine transitions."""
    try:
        curr_enum = LegalFindingStatus(current)
        target_enum = LegalFindingStatus(target)
    except ValueError:
        raise ValueError(f"Invalid finding status. Current: '{current}', Target: '{target}'")

    if curr_enum == target_enum:
        return

    allowed = VALID_FINDING_TRANSITIONS.get(curr_enum, set())
    if target_enum not in allowed:
        allowed_names = [s.value for s in allowed]
        raise ValueError(
            f"Illegal legal finding transition from '{curr_enum.value}' to '{target_enum.value}'. Allowed: {allowed_names}"
        )
