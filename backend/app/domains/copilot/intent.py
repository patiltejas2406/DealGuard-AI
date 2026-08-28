"""DealGuard AI Copilot: Natural Language Intent Recognition and Language Routing Layer."""

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class CopilotIntent(str, Enum):
    FINANCIAL_ANALYSIS = "FINANCIAL_ANALYSIS"
    QOE_ANALYSIS = "QOE_ANALYSIS"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    LEGAL_ANALYSIS = "LEGAL_ANALYSIS"
    TECHNOLOGY_ANALYSIS = "TECHNOLOGY_ANALYSIS"
    VALUATION = "VALUATION"
    SYNERGY_ANALYSIS = "SYNERGY_ANALYSIS"
    INTEGRATION = "INTEGRATION"
    POST_ACQUISITION = "POST_ACQUISITION"
    INVESTMENT_DECISION = "INVESTMENT_DECISION"
    GENERAL_DEAL_INTELLIGENCE = "GENERAL_DEAL_INTELLIGENCE"
    FOLLOW_UP = "FOLLOW_UP"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class CopilotLanguage(str, Enum):
    ENGLISH = "ENGLISH"
    HINGLISH = "HINGLISH"


# Hinglish / Hindi lexical markers
HINGLISH_MARKERS = [
    r"\bdeal\s+karen\b",
    r"\bdeal\s+karein\b",
    r"\bkaren\b",
    r"\bkarein\b",
    r"\bnahi\b",
    r"\bkya\b",
    r"\bbhai\b",
    r"\bhai\b",
    r"\bhain\b",
    r"\bdikkat\b",
    r"\bsahi\b",
    r"\bbaad\b",
    r"\bchahiye\b",
    r"\bscene\b",
    r"\bkyun\b",
    r"\bagar\b",
    r"\btoh\b",
    r"\bkaise\b",
    r"\bkaisa\b",
    r"\bkaisi\b",
    r"\bhoga\b",
    r"\bhogi\b",
    r"\bye\b",
    r"\byeh\b",
    r"\bis\s+deal\b",
    r"\biska\b",
    r"\biski\b",
    r"\bmein\b",
    r"\bme\b",
    r"\bpe\b",
    r"\bleni\b",
    r"\blena\b",
    r"\bkhatra\b",
    r"\bnuksan\b",
    r"\bpaisa\b",
    r"\bbatao\b",
    r"\bsamjhao\b",
    r"\bkaro\b",
    r"\bkarna\b",
    r"\bkahaan\b",
    r"\bwala\b",
    r"\bwali\b",
    r"\btheek\b",
    r"\blafda\b",
]

HINGLISH_REGEX = re.compile("|".join(HINGLISH_MARKERS), re.IGNORECASE)


# Intent keyword and regex definitions
INTENT_PATTERNS: Dict[CopilotIntent, List[re.Pattern]] = {
    CopilotIntent.INVESTMENT_DECISION: [
        re.compile(r"\b(should\s+we\s+(buy|acquire|proceed|invest))\b", re.IGNORECASE),
        re.compile(r"\b(buy\s+this\s+company|acquire\s+this\s+company)\b", re.IGNORECASE),
        re.compile(r"\b(investment\s+decision|acquisition\s+decision|deal\s+recommendation)\b", re.IGNORECASE),
        re.compile(r"\b(buy\s+or\s+pass|go\s+or\s+no\s*go|proceed\s+with\s+deal)\b", re.IGNORECASE),
        re.compile(r"\bdeal\s+karen\s+ya\s+nahi\b", re.IGNORECASE),
        re.compile(r"\bdeal\s+karein\s+ya\s+nahi\b", re.IGNORECASE),
        re.compile(r"\bdeal\s+karna\s+chahiye\b", re.IGNORECASE),
        re.compile(r"\bdeal\s+karein\s+kya\b", re.IGNORECASE),
        re.compile(r"\byeh?\s+company\s+leni\s+chahiye\b", re.IGNORECASE),
        re.compile(r"\bcompany\s+buy\s+karni\s+chahiye\b", re.IGNORECASE),
        re.compile(r"\bis\s+deal\s+mein\s+invest\s+karein\b", re.IGNORECASE),
        re.compile(r"\bdeal\s+final\s+karein\b", re.IGNORECASE),
    ],
    CopilotIntent.RISK_ANALYSIS: [
        re.compile(r"\b(biggest\s+risk|major\s+risk|top\s+risk|key\s+risk|risk\s+profile|deal\s+risks?|downside|vulnerability|threats?)\b", re.IGNORECASE),
        re.compile(r"\b(what\s+are\s+the\s+(biggest\s+)?risks?|why\s+is\s+this\s+deal\s+risky)\b", re.IGNORECASE),
        re.compile(r"\bsabse\s+bada\s+risk\b", re.IGNORECASE),
        re.compile(r"\b(bada\s+risk|deal\s+mein\s+risk|kya\s+khatra\s+hai|khatra|kya\s+downside|kya\s+nuksan)\b", re.IGNORECASE),
        re.compile(r"\brisks?\s+ka\s+scene\b", re.IGNORECASE),
    ],
    CopilotIntent.QOE_ANALYSIS: [
        re.compile(r"\b(normalized\s+ebitda|qoe|quality\s+of\s+earnings|ebitda\s+adjustment|qoe\s+adjustments?)\b", re.IGNORECASE),
        re.compile(r"\b(qoe\s+ka\s+scene|normalized\s+ebitda\s+kya\s+hai)\b", re.IGNORECASE),
    ],
    CopilotIntent.FINANCIAL_ANALYSIS: [
        re.compile(r"\b(financial\s+condition|financial\s+performance|financial\s+health|financials?|ebitda|revenue|cash\s+flow|margin|balance\s+sheet|p&l|profitability)\b", re.IGNORECASE),
        re.compile(r"\b(financials?\s+ka\s+scene|financial\s+condition\s+kaisi\b|financials\s+kaise\s+hain|financial\s+angle)\b", re.IGNORECASE),
        re.compile(r"\b(financially\s+kaisa\s+hai|kamai\s+kaisi\s+hai|revenue\s+kitna\s+hai|financials?\s+batao)\b", re.IGNORECASE),
    ],
    CopilotIntent.LEGAL_ANALYSIS: [
        re.compile(r"\b(legal|contracts?|change\s+of\s+control|consent|clauses?|litigation|compliance|gdpr|counterparty|indemnity)\b", re.IGNORECASE),
        re.compile(r"\b(legal\s+mein\s+kya\s+dikkat|legal\s+issue|contract\s+mein\s+kya\s+dikkat|change\s+of\s+control\s+ka\s+lafda|legal\s+scene)\b", re.IGNORECASE),
    ],
    CopilotIntent.TECHNOLOGY_ANALYSIS: [
        re.compile(r"\b(tech|technology|tech\s+stack|architecture|cloud|aws|infra|infrastructure|sla|uptime|spof|single\s+point\s+of\s+failure|technical\s+debt|monolith)\b", re.IGNORECASE),
        re.compile(r"\b(tech\s+side\s+pe\s+kya\s+issue|tech\s+scene\s+kaisa|tech\s+mein\s+kya\s+dikkat|architecture\s+kaisa|system\s+down)\b", re.IGNORECASE),
    ],
    CopilotIntent.VALUATION: [
        re.compile(r"\b(valuation|dcf|discounted\s+cash\s+flow|comparables?|multiples?|ev/ebitda|target\s+ev|enterprise\s+value|fair\s+value|overvalued|undervalued)\b", re.IGNORECASE),
        re.compile(r"\b(valuation\s+sahi\s+hai\s+kya|valuation\s+theek\s+hai\s+kya|valuation\s+justifiable|sahi\s+daam|price\s+sahi)\b", re.IGNORECASE),
    ],
    CopilotIntent.POST_ACQUISITION: [
        re.compile(r"\b(post[- ]acquisition|after\s+acquisition|100[- ]day|first\s+30\s+days|first\s+100\s+days|day\s+1\s+priorities|post[- ]close)\b", re.IGNORECASE),
        re.compile(r"\b(acquisition\s+ke\s+baad|deal\s+ke\s+baad|close\s+hone\s+ke\s+baad|post[- ]acquisition\s+kya)\b", re.IGNORECASE),
    ],
    CopilotIntent.INTEGRATION: [
        re.compile(r"\b(integration|workstream|milestones?|critical\s+path|blockers?|day\s+1\s+readiness)\b", re.IGNORECASE),
        re.compile(r"\b(integration\s+kaise\s+hoga|100[- ]day\s+plan\s+kya\s+hai|shuru\s+mein\s+kya\s+karna)\b", re.IGNORECASE),
    ],
    CopilotIntent.SYNERGY_ANALYSIS: [
        re.compile(r"\b(synerg(y|ies)|value\s+creation|cost\s+savings|cross[- ]sell|run[- ]rate\s+synerg)\b", re.IGNORECASE),
        re.compile(r"\b(synergy\s+kya\s+hai|cost\s+savings\s+kahaan|value\s+creation\s+kaise)\b", re.IGNORECASE),
    ],
    CopilotIntent.FOLLOW_UP: [
        re.compile(r"^\s*(why\??|why\s+so\??|explain\s+why\??|kyun\??|kyu\??|aisa\s+kyun\??|reason\s+kya\s+hai\??)\s*$", re.IGNORECASE),
        re.compile(r"\b(agar\s+ye\s+risk\s+solve\s+ho\s+jaye\s+toh|what\s+if\s+this\s+risk\s+is\s+(solved|mitigated|fixed)|agar\s+risk\s+fix\s+ho\s+jaye)\b", re.IGNORECASE),
    ],
}

# Domain routing mapping
INTENT_DOMAIN_ROUTING: Dict[CopilotIntent, List[str]] = {
    CopilotIntent.INVESTMENT_DECISION: [
        "DECISION_SCORE",
        "FINANCIALS",
        "QOE",
        "RISKS",
        "VALUATION",
        "LEGAL_CONTRACTS",
        "TECHNOLOGY_OPERATIONS",
        "SYNERGIES",
        "INTEGRATION",
        "DOCUMENTS",
    ],
    CopilotIntent.RISK_ANALYSIS: [
        "RISKS",
        "FINANCIALS",
        "LEGAL_CONTRACTS",
        "TECHNOLOGY_OPERATIONS",
        "DOCUMENTS",
    ],
    CopilotIntent.FINANCIAL_ANALYSIS: [
        "FINANCIALS",
        "QOE",
        "DOCUMENTS",
    ],
    CopilotIntent.QOE_ANALYSIS: [
        "QOE",
        "FINANCIALS",
        "DOCUMENTS",
    ],
    CopilotIntent.LEGAL_ANALYSIS: [
        "LEGAL_CONTRACTS",
        "DOCUMENTS",
        "RISKS",
    ],
    CopilotIntent.TECHNOLOGY_ANALYSIS: [
        "TECHNOLOGY_OPERATIONS",
        "DOCUMENTS",
        "RISKS",
    ],
    CopilotIntent.VALUATION: [
        "VALUATION",
        "FINANCIALS",
        "DOCUMENTS",
    ],
    CopilotIntent.POST_ACQUISITION: [
        "INTEGRATION",
        "SYNERGIES",
        "TECHNOLOGY_OPERATIONS",
        "FINANCIALS",
        "RISKS",
    ],
    CopilotIntent.INTEGRATION: [
        "INTEGRATION",
        "SYNERGIES",
        "TECHNOLOGY_OPERATIONS",
        "DOCUMENTS",
    ],
    CopilotIntent.SYNERGY_ANALYSIS: [
        "SYNERGIES",
        "FINANCIALS",
        "INTEGRATION",
        "DOCUMENTS",
    ],
    CopilotIntent.GENERAL_DEAL_INTELLIGENCE: [
        "DOCUMENTS",
        "FINANCIALS",
        "RISKS",
        "LEGAL_CONTRACTS",
        "TECHNOLOGY_OPERATIONS",
    ],
    CopilotIntent.FOLLOW_UP: [
        "DECISION_SCORE",
        "FINANCIALS",
        "RISKS",
        "LEGAL_CONTRACTS",
        "TECHNOLOGY_OPERATIONS",
        "DOCUMENTS",
    ],
    CopilotIntent.INSUFFICIENT_EVIDENCE: [
        "DOCUMENTS",
    ],
}


class IntentRouter:
    """Classifies user queries by intent and language, and computes target domain routing."""

    @staticmethod
    def detect_language(query: str) -> CopilotLanguage:
        """Detect whether input is in English or Hinglish/Hindi."""
        if not query:
            return CopilotLanguage.ENGLISH
        if HINGLISH_REGEX.search(query):
            return CopilotLanguage.HINGLISH
        return CopilotLanguage.ENGLISH

    @classmethod
    def classify_intent(
        cls, query: str, conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> CopilotIntent:
        """Identify conversational intent using pattern matching and multi-turn context."""
        cleaned = query.strip()
        if not cleaned:
            return CopilotIntent.INSUFFICIENT_EVIDENCE

        # 1. Check Follow-Up patterns first
        for pattern in INTENT_PATTERNS[CopilotIntent.FOLLOW_UP]:
            if pattern.search(cleaned):
                return CopilotIntent.FOLLOW_UP

        # 2. Check specific domain and decision intents
        # Priority order: INVESTMENT_DECISION -> QOE -> FINANCIAL -> RISK -> LEGAL -> TECH -> VALUATION -> POST_ACQUISITION -> SYNERGY -> INTEGRATION
        priority_order = [
            CopilotIntent.INVESTMENT_DECISION,
            CopilotIntent.QOE_ANALYSIS,
            CopilotIntent.FINANCIAL_ANALYSIS,
            CopilotIntent.RISK_ANALYSIS,
            CopilotIntent.LEGAL_ANALYSIS,
            CopilotIntent.TECHNOLOGY_ANALYSIS,
            CopilotIntent.VALUATION,
            CopilotIntent.POST_ACQUISITION,
            CopilotIntent.SYNERGY_ANALYSIS,
            CopilotIntent.INTEGRATION,
        ]

        for intent in priority_order:
            patterns = INTENT_PATTERNS.get(intent, [])
            for pattern in patterns:
                if pattern.search(cleaned):
                    return intent

        # Fallback to general intelligence
        return CopilotIntent.GENERAL_DEAL_INTELLIGENCE

    @classmethod
    def get_candidate_domains(cls, intent: CopilotIntent) -> List[str]:
        """Return candidate retrieval domains mapped to the given intent."""
        return INTENT_DOMAIN_ROUTING.get(
            intent, INTENT_DOMAIN_ROUTING[CopilotIntent.GENERAL_DEAL_INTELLIGENCE]
        )

    @classmethod
    def route_query(
        cls, query: str, conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[CopilotIntent, CopilotLanguage, List[str]]:
        """Route user query to appropriate intent, language mode, and candidate domain list."""
        intent = cls.classify_intent(query, conversation_history)
        language = cls.detect_language(query)
        candidate_domains = cls.get_candidate_domains(intent)
        return intent, language, candidate_domains
