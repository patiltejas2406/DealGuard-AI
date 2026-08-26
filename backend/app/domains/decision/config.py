"""Centralized Configuration, Decision Bands, and Calibration Weights for Decision Score Engine."""

from enum import Enum
from typing import Dict


class DecisionBand(str, Enum):
    """Calibrated decision assessment bands for composite investment scores."""
    STRONG = "STRONG"            # 80 - 100: Prime candidate with superior risk-adjusted return profile
    FAVORABLE = "FAVORABLE"      # 65 - 79: Solid investment profile with standard diligence conditions
    CAUTION = "CAUTION"          # 50 - 64: Viable but requires structured covenants or price renegotiation
    HIGH_RISK = "HIGH_RISK"      # 35 - 49: Significant structural downside risks or valuation dislocation
    AVOID = "AVOID"              # 0 - 34: Severe deal-breaking risks / excessive vulnerability


class DataAvailabilityStatus(str, Enum):
    """Confidence coverage status for scoring components."""
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


# Current Authoritative Decision Engine Version
CURRENT_SCORING_VERSION = "1.0"

# Initial Product & Research Default Weights (Sum = 1.00)
DEFAULT_COMPONENT_WEIGHTS: Dict[str, float] = {
    "FINANCIAL_HEALTH": 0.25,
    "VALUATION_ATTRACTIVENESS": 0.20,
    "RISK_EXPOSURE": 0.25,
    "REVENUE_QUALITY": 0.10,
    "EVIDENCE_CONFIDENCE": 0.10,
    "DEAL_COMPLEXITY": 0.10,
}

# Decision Band Classification Thresholds
DECISION_BAND_THRESHOLDS = [
    (80.0, DecisionBand.STRONG, "Strong Candidate — High risk-adjusted quality across financial, risk, and valuation pillars."),
    (65.0, DecisionBand.FAVORABLE, "Favorable — Attractive acquisition profile subject to standard confirmatory closing covenants."),
    (50.0, DecisionBand.CAUTION, "Caution — Moderate quality; recommends purchase price adjustment or targeted escrow terms."),
    (35.0, DecisionBand.HIGH_RISK, "High Risk — Substantial risk exposure or valuation overpayment identified; proceed with caution."),
    (0.0, DecisionBand.AVOID, "Avoid — Critical risk exposures or severe structural deficiencies; deal not recommended."),
]


def classify_decision_band(score: float) -> DecisionBand:
    """Classify a 0-100 composite score into a calibrated decision band."""
    clamped_score = max(0.0, min(100.0, float(score)))
    for threshold, band, _ in DECISION_BAND_THRESHOLDS:
        if clamped_score >= threshold:
            return band
    return DecisionBand.AVOID


def get_band_description(band: DecisionBand) -> str:
    """Return institutional description for a decision band."""
    for _, b, desc in DECISION_BAND_THRESHOLDS:
        if b == band:
            return desc
    return "Institutional decision evaluation."
