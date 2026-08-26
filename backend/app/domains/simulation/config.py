"""Centralized Configuration, Variable Whitelist, and Distribution Bounds for Simulation Engine."""

from enum import Enum
from typing import Any, Dict, Optional


class ScenarioType(str, Enum):
    """Supported scenario classifications."""
    WHAT_IF = "WHAT_IF"
    DOWNSIDE = "DOWNSIDE"
    UPSIDE = "UPSIDE"
    STRESS_TEST = "STRESS_TEST"
    SENSITIVITY = "SENSITIVITY"


class DistributionType(str, Enum):
    """Supported probability distributions for Monte Carlo simulation."""
    NORMAL = "NORMAL"
    TRIANGULAR = "TRIANGULAR"
    UNIFORM = "UNIFORM"
    LOGNORMAL = "LOGNORMAL"


# Engine Versions
SCENARIO_ENGINE_VERSION = "1.0"
MONTE_CARLO_ENGINE_VERSION = "1.0"

# Simulation Bounds
DEFAULT_MONTE_CARLO_ITERATIONS = 1000
MAX_MONTE_CARLO_ITERATIONS = 50000
MIN_MONTE_CARLO_ITERATIONS = 100

# Whitelisted Scenario Simulation Variables
WHITELISTED_VARIABLES: Dict[str, Dict[str, Any]] = {
    "revenue_growth_pct": {
        "label": "Revenue Growth Rate (%)",
        "category": "FINANCIAL",
        "unit": "PERCENTAGE",
        "min": -100.0,
        "max": 500.0,
        "default_step": 2.0,
    },
    "revenue_multiplier": {
        "label": "Revenue Shocker (x)",
        "category": "FINANCIAL",
        "unit": "MULTIPLIER",
        "min": 0.1,
        "max": 3.0,
        "default_step": 0.05,
    },
    "ebitda_margin_pct": {
        "label": "EBITDA Margin (%)",
        "category": "FINANCIAL",
        "unit": "PERCENTAGE",
        "min": -50.0,
        "max": 85.0,
        "default_step": 2.0,
    },
    "wacc_pct": {
        "label": "Discount Rate / WACC (%)",
        "category": "VALUATION",
        "unit": "PERCENTAGE",
        "min": 0.5,
        "max": 35.0,
        "default_step": 0.5,
    },
    "terminal_growth_rate_pct": {
        "label": "Terminal Growth Rate (%)",
        "category": "VALUATION",
        "unit": "PERCENTAGE",
        "min": -5.0,
        "max": 15.0,
        "default_step": 0.25,
    },
    "exit_multiple": {
        "label": "Exit EV/EBITDA Multiple (x)",
        "category": "VALUATION",
        "unit": "MULTIPLE",
        "min": 1.0,
        "max": 40.0,
        "default_step": 0.5,
    },
    "purchase_price": {
        "label": "Transaction Purchase Price (Target EV)",
        "category": "VALUATION",
        "unit": "CURRENCY",
        "min": 0.0,
        "max": 1e12,
        "default_step": 1000000.0,
    },
    "churn_rate_pct": {
        "label": "Annual Customer Churn Rate (%)",
        "category": "REVENUE_QUALITY",
        "unit": "PERCENTAGE",
        "min": 0.0,
        "max": 100.0,
        "default_step": 1.0,
    },
    "customer_concentration_pct": {
        "label": "Top Customer Revenue Concentration (%)",
        "category": "RISK",
        "unit": "PERCENTAGE",
        "min": 0.0,
        "max": 100.0,
        "default_step": 5.0,
    },
    "synergy_value": {
        "label": "Annual Run-Rate Cost Synergies",
        "category": "VALUE_CREATION",
        "unit": "CURRENCY",
        "min": 0.0,
        "max": 1e11,
        "default_step": 500000.0,
    },
    "synergy_realization_rate_pct": {
        "label": "Synergy Realization Rate (%)",
        "category": "VALUE_CREATION",
        "unit": "PERCENTAGE",
        "min": 0.0,
        "max": 100.0,
        "default_step": 10.0,
    },
    "integration_cost": {
        "label": "One-Time Integration CapEx / OpEx",
        "category": "VALUE_CREATION",
        "unit": "CURRENCY",
        "min": 0.0,
        "max": 1e11,
        "default_step": 500000.0,
    },
}


def validate_variable_value(name: str, value: float) -> float:
    """Validate that a variable is whitelisted and within mathematical bounds."""
    if name not in WHITELISTED_VARIABLES:
        raise ValueError(f"Variable '{name}' is not in the supported simulation whitelist.")

    meta = WHITELISTED_VARIABLES[name]
    min_val = meta["min"]
    max_val = meta["max"]

    if value < min_val or value > max_val:
        raise ValueError(
            f"Variable '{name}' value {value} is out of permitted range [{min_val}, {max_val}]."
        )
    return float(value)
