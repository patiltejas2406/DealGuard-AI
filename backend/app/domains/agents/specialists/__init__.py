"""Specialist Intelligence Agents Registry."""

from app.domains.agents.specialists.finance import FinanceIntelligenceAgent
from app.domains.agents.specialists.valuation import ValuationAgent
from app.domains.agents.specialists.risk import RiskIntelligenceAgent
from app.domains.agents.specialists.legal import LegalIntelligenceAgent
from app.domains.agents.specialists.technology import TechnologyOperationsAgent
from app.domains.agents.specialists.scenario import ScenarioSimulationAgent
from app.domains.agents.specialists.integration import IntegrationIntelligenceAgent
from app.domains.agents.specialists.synergy import SynergyValueCreationAgent

__all__ = [
    "FinanceIntelligenceAgent",
    "ValuationAgent",
    "RiskIntelligenceAgent",
    "LegalIntelligenceAgent",
    "TechnologyOperationsAgent",
    "ScenarioSimulationAgent",
    "IntegrationIntelligenceAgent",
    "SynergyValueCreationAgent",
]
