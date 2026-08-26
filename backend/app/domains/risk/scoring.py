"""Pure-Python Deterministic Risk Scoring and Matrix Computation Engine."""

from typing import Any, Dict, List, Tuple
from app.domains.risk.taxonomy import RiskCategory, RiskLevel


class RiskScoringError(ValueError):
    """Raised when risk scoring parameters violate quantitative bounds."""
    pass


def validate_score_inputs(severity: int, likelihood: int) -> None:
    """Validate severity and likelihood are integer values between 1 and 5."""
    if not isinstance(severity, int) or severity < 1 or severity > 5:
        raise RiskScoringError(f"Severity must be an integer between 1 and 5, received {severity}.")
    if not isinstance(likelihood, int) or likelihood < 1 or likelihood > 5:
        raise RiskScoringError(f"Likelihood must be an integer between 1 and 5, received {likelihood}.")


def compute_risk_score(severity: int, likelihood: int) -> int:
    """
    Calculate deterministic risk score:
    Score = Severity (1..5) * Likelihood (1..5) -> Range [1, 25]
    """
    validate_score_inputs(severity, likelihood)
    return severity * likelihood


def determine_risk_level(score: int) -> RiskLevel:
    """
    Map quantitative risk score to institutional tier:
    - 1 to 4: LOW
    - 5 to 9: MODERATE
    - 10 to 14: HIGH
    - 15 to 25: CRITICAL
    """
    if score < 1 or score > 25:
        raise RiskScoringError(f"Risk score must be between 1 and 25, received {score}.")
    
    if score <= 4:
        return RiskLevel.LOW
    elif score <= 9:
        return RiskLevel.MODERATE
    elif score <= 14:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def calculate_risk_evaluation(severity: int, likelihood: int) -> Tuple[int, RiskLevel]:
    """Calculate score and risk level simultaneously."""
    score = compute_risk_score(severity, likelihood)
    level = determine_risk_level(score)
    return score, level


def compute_risk_matrix(risks: List[Any]) -> Dict[str, Any]:
    """
    Aggregate a list of risk items into a 5x5 Likelihood x Severity matrix,
    category distribution, and risk level summary statistics.
    """
    # 5x5 Matrix: grid[likelihood][severity] -> list of risk IDs/summaries
    # likelihood: 1 (bottom) to 5 (top)
    # severity: 1 (left) to 5 (right)
    grid: Dict[int, Dict[int, List[Dict[str, Any]]]] = {
        l: {s: [] for s in range(1, 6)} for l in range(1, 6)
    }

    level_counts = {
        RiskLevel.LOW.value: 0,
        RiskLevel.MODERATE.value: 0,
        RiskLevel.HIGH.value: 0,
        RiskLevel.CRITICAL.value: 0,
    }

    category_counts: Dict[str, int] = {cat.value: 0 for cat in RiskCategory}
    status_counts: Dict[str, int] = {}
    total_score = 0

    for r in risks:
        s = getattr(r, "severity", 1)
        l = getattr(r, "likelihood", 1)
        score = getattr(r, "score", s * l)
        level_str = getattr(r, "risk_level", None) or determine_risk_level(score).value
        category_str = getattr(r, "category", "GENERAL")
        status_str = getattr(r, "status", "IDENTIFIED")

        # Clamp bounds defensively if legacy data exists
        s_clamped = max(1, min(5, s))
        l_clamped = max(1, min(5, l))

        risk_brief = {
            "id": str(getattr(r, "id", "")),
            "title": getattr(r, "title", ""),
            "category": category_str,
            "severity": s_clamped,
            "likelihood": l_clamped,
            "score": score,
            "risk_level": level_str,
            "status": status_str,
        }

        grid[l_clamped][s_clamped].append(risk_brief)

        if level_str in level_counts:
            level_counts[level_str] += 1

        if category_str in category_counts:
            category_counts[category_str] += 1
        else:
            category_counts[category_str] = 1

        status_counts[status_str] = status_counts.get(status_str, 0) + 1
        total_score += score

    total_risks = len(risks)
    avg_score = round(total_score / total_risks, 2) if total_risks > 0 else 0.0

    return {
        "total_risks": total_risks,
        "average_score": avg_score,
        "level_counts": level_counts,
        "category_counts": category_counts,
        "status_counts": status_counts,
        "matrix_grid": grid,
    }
