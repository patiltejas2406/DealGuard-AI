"""17-Pillar M&A Risk Taxonomy, Metadata, and Detection Heuristics."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class RiskCategory(str, Enum):
    """Institutional 17 Diligence & Risk Pillars."""
    CUSTOMER_CONCENTRATION = "CUSTOMER_CONCENTRATION"
    KEY_PERSON = "KEY_PERSON"
    LEGAL_LITIGATION = "LEGAL_LITIGATION"
    REGULATORY = "REGULATORY"
    CYBERSECURITY = "CYBERSECURITY"
    TECHNOLOGY_DEBT = "TECHNOLOGY_DEBT"
    ESG = "ESG"
    RESTATEMENT = "RESTATEMENT"
    SUPPLY_CHAIN = "SUPPLY_CHAIN"
    IP_INFRINGEMENT = "IP_INFRINGEMENT"
    TAX = "TAX"
    MACRO_FX = "MACRO_FX"
    LABOR_WORKFORCE = "LABOR_WORKFORCE"
    CHANGE_OF_CONTROL = "CHANGE_OF_CONTROL"
    DEBT_COVENANTS = "DEBT_COVENANTS"
    REVENUE_QUALITY = "REVENUE_QUALITY"
    INTEGRATION_COMPLEXITY = "INTEGRATION_COMPLEXITY"


class RiskLevel(str, Enum):
    """Risk severity classification determined by quantitative score."""
    LOW = "LOW"            # Score 1 - 4
    MODERATE = "MODERATE"  # Score 5 - 9
    HIGH = "HIGH"          # Score 10 - 14
    CRITICAL = "CRITICAL"  # Score 15 - 25


class RiskStatus(str, Enum):
    """Lifecycle status of an identified risk item."""
    IDENTIFIED = "IDENTIFIED"
    REVIEWED = "REVIEWED"
    ACCEPTED = "ACCEPTED"
    MITIGATED = "MITIGATED"
    REJECTED = "REJECTED"


class DetectionSource(str, Enum):
    """Origin of the risk identification."""
    AI_EXTRACTED = "AI_EXTRACTED"
    MANUAL_ENTRY = "MANUAL_ENTRY"
    SYSTEM_RULE = "SYSTEM_RULE"


@dataclass(frozen=True)
class CategoryInfo:
    """Metadata describing a risk pillar, including detection signals and default mitigation."""
    id: str
    name: str
    description: str
    signals: List[str]
    default_mitigation: str
    typical_severity_range: str


CATEGORY_METADATA: Dict[RiskCategory, CategoryInfo] = {
    RiskCategory.CUSTOMER_CONCENTRATION: CategoryInfo(
        id="CUSTOMER_CONCENTRATION",
        name="Customer Concentration",
        description="High dependency on top customers, accounts, or channel partners exposing the business to major revenue cliff risks.",
        signals=["top customer", "concentration", "largest customer", "top 3 accounts", "revenue dependency", "single client", "customer loss"],
        default_mitigation="Structure purchase price with milestone-based earnouts, require key customer contract renewals prior to close, and accelerate account diversification.",
        typical_severity_range="3 - 5",
    ),
    RiskCategory.KEY_PERSON: CategoryInfo(
        id="KEY_PERSON",
        name="Key Person & Founder Dependency",
        description="Over-reliance on founders, executive leadership, or single critical engineers with unique operational or domain knowledge.",
        signals=["founder dependent", "key employee", "sole developer", "succession plan", "non-compete", "retention risk", "management retention"],
        default_mitigation="Implement 36-month equity vesting retention packages, execute strict non-solicitation/non-compete agreements, and establish cross-training documentation.",
        typical_severity_range="3 - 4",
    ),
    RiskCategory.LEGAL_LITIGATION: CategoryInfo(
        id="LEGAL_LITIGATION",
        name="Legal & Litigation Exposure",
        description="Active, pending, or threatened litigation, contract disputes, indemnification claims, or contingent legal liabilities.",
        signals=["lawsuit", "litigation", "arbitration", "subpoena", "dispute", "settlement", "indemnity", "legal claim"],
        default_mitigation="Require special indemnity escrows, specific pre-closing litigation settlements, or buy-side Representations & Warranties (R&W) insurance carve-outs.",
        typical_severity_range="2 - 5",
    ),
    RiskCategory.REGULATORY: CategoryInfo(
        id="REGULATORY",
        name="Regulatory Compliance & Licensing",
        description="Compliance deficiencies, licensing vulnerabilities, antitrust scrutiny, or exposure to evolving governmental regulations.",
        signals=["compliance", "regulatory fine", "sanction", "license suspension", "ftc", "sec", "gdpr", "hipaa", "antitrust"],
        default_mitigation="Engage specialized regulatory counsel, condition closing on regulatory approvals/licenses, and budget for ongoing compliance remediation.",
        typical_severity_range="3 - 5",
    ),
    RiskCategory.CYBERSECURITY: CategoryInfo(
        id="CYBERSECURITY",
        name="Cybersecurity & Data Privacy",
        description="Vulnerabilities in information security posture, unpatched infrastructure, past data breaches, or non-compliance with SOC2/ISO27001.",
        signals=["data breach", "ransomware", "vulnerability", "soc 2", "penetration test", "cyber incident", "iso 27001", "unencrypted"],
        default_mitigation="Mandate post-close SOC2 Type II certification, conduct comprehensive third-party penetration testing, and expand cyber liability insurance coverage.",
        typical_severity_range="3 - 5",
    ),
    RiskCategory.TECHNOLOGY_DEBT: CategoryInfo(
        id="TECHNOLOGY_DEBT",
        name="Technology Debt & Scalability",
        description="Legacy software architectures, unsupported programming languages/frameworks, monolithic bottlenecks, and high maintenance overhead.",
        signals=["legacy system", "monolith", "end of life", "unsupported library", "refactoring needed", "scalability bottleneck", "technical debt"],
        default_mitigation="Carve out dedicated CapEx budget for cloud modernization, decouple monolithic services into scalable microservices, and automate CI/CD testing.",
        typical_severity_range="2 - 4",
    ),
    RiskCategory.ESG: CategoryInfo(
        id="ESG",
        name="ESG & Environmental Liability",
        description="Environmental contamination liabilities, workplace safety infractions, labor standard deficiencies, or governance irregularities.",
        signals=["environmental fine", "emissions", "workplace safety", "osha", "governance violation", "carbon tax", "hazardous waste"],
        default_mitigation="Perform Phase I/Phase II Environmental Site Assessments, implement institutional ESG reporting frameworks, and establish strict workplace safety protocols.",
        typical_severity_range="2 - 4",
    ),
    RiskCategory.RESTATEMENT: CategoryInfo(
        id="RESTATEMENT",
        name="Financial Restatement & Internal Controls",
        description="Accounting errors, restatements, auditor turnover, material weaknesses in internal controls, or non-GAAP discrepancies.",
        signals=["restatement", "material weakness", "internal controls", "auditor resignation", "accounting adjustment", "sox deficiency"],
        default_mitigation="Perform a comprehensive Quality of Earnings (QoE) audit, institute independent board audit committee oversight, and upgrade ERP ledger controls.",
        typical_severity_range="4 - 5",
    ),
    RiskCategory.SUPPLY_CHAIN: CategoryInfo(
        id="SUPPLY_CHAIN",
        name="Supply Chain & Vendor Dependency",
        description="Single-source supplier vulnerability, critical hardware/component shortages, long lead times, or geographic supplier concentration.",
        signals=["single source supplier", "vendor concentration", "supply disruption", "component shortage", "lead time", "supplier delay"],
        default_mitigation="Dual-source critical component vendors, establish safety stock buffer inventory, and negotiate long-term fixed price Master Service Agreements.",
        typical_severity_range="3 - 4",
    ),
    RiskCategory.IP_INFRINGEMENT: CategoryInfo(
        id="IP_INFRINGEMENT",
        name="Intellectual Property & Licensing",
        description="Patent, trademark, or copyright infringement claims, unassigned IP rights from contractors/founders, or copyleft open-source (GPL/AGPL) contamination.",
        signals=["patent infringement", "ip dispute", "trademark claim", "gpl license", "proprietary code", "unassigned ip", "contractor assignment"],
        default_mitigation="Execute retroactive IP assignment agreements with all historical contributors, conduct automated Black Duck / FOSSA open-source scans, and obtain patent defense insurance.",
        typical_severity_range="3 - 5",
    ),
    RiskCategory.TAX: CategoryInfo(
        id="TAX",
        name="Tax Exposure & Transfer Pricing",
        description="Uncertain tax positions, state sales tax nexus liabilities (Wayfair), transfer pricing audits, or aggressive deductions.",
        signals=["tax audit", "unpaid taxes", "sales tax nexus", "transfer pricing", "irs inquiry", "tax penalty", "withholding tax"],
        default_mitigation="Quantify tax nexus exposure in pre-closing QoE, establish dedicated special tax indemnity escrow, and file voluntary disclosure agreements (VDAs).",
        typical_severity_range="2 - 4",
    ),
    RiskCategory.MACRO_FX: CategoryInfo(
        id="MACRO_FX",
        name="Macroeconomic & Foreign Exchange",
        description="Unhedged foreign currency exchange volatility, floating interest rate debt exposure, commodity inflation, or geopolitical trade tariffs.",
        signals=["fx exposure", "foreign currency", "interest rate risk", "inflation impact", "tariff", "geopolitical disruption", "currency hedge"],
        default_mitigation="Execute FX forward contracts/hedges for cross-border revenues and fix interest rates on variable debt using interest rate swap derivatives.",
        typical_severity_range="2 - 4",
    ),
    RiskCategory.LABOR_WORKFORCE: CategoryInfo(
        id="LABOR_WORKFORCE",
        name="Labor & Workforce Relations",
        description="Unionization conflicts, high employee turnover, wage-and-hour collective disputes, or independent contractor misclassification risk.",
        signals=["union", "strike", "turnover rate", "labor dispute", "contractor misclassification", "overtime lawsuit", "wage claim"],
        default_mitigation="Audit contractor classifications against FLSA/state standards, benchmark compensation to median market rates, and formulate constructive labor engagement strategies.",
        typical_severity_range="2 - 4",
    ),
    RiskCategory.CHANGE_OF_CONTROL: CategoryInfo(
        id="CHANGE_OF_CONTROL",
        name="Change of Control & Contractual Termination",
        description="Commercial or vendor contracts containing change-of-control termination triggers, consent mandates, or penalty clauses upon acquisition.",
        signals=["change of control", "assignment consent", "termination on acquisition", "notice of merger", "contractual consent"],
        default_mitigation="Draft pre-closing consent solicitation schedule, condition transaction closing on key client consent milestones, and prepare bilateral amendment waivers.",
        typical_severity_range="3 - 5",
    ),
    RiskCategory.DEBT_COVENANTS: CategoryInfo(
        id="DEBT_COVENANTS",
        name="Debt Covenants & Liquidity Solvency",
        description="Leverage ratio (Debt/EBITDA) covenant proximity, minimum liquidity thresholds, debt acceleration triggers, and near-term debt maturity cliffs.",
        signals=["debt covenant", "leverage ratio", "liquidity covenant", "default event", "debt maturity", "accelerated debt", "credit facility breach"],
        default_mitigation="Refinance high-coupon mezzanine debt with syndicated bank facilities, negotiate relaxed post-deal covenant headroom, and model cash buffers under stress scenarios.",
        typical_severity_range="4 - 5",
    ),
    RiskCategory.REVENUE_QUALITY: CategoryInfo(
        id="REVENUE_QUALITY",
        name="Revenue Quality & Churn Deficiencies",
        description="Aggressive upfront revenue recognition, non-recurring consulting disguised as recurring ARR, deteriorating net retention rate (NDR), or high gross churn.",
        signals=["churn rate", "non recurring revenue", "deferred revenue", "revenue recognition", "net retention", "cancellation", "arr quality"],
        default_mitigation="Re-underwrite DCF and valuation multiples strictly on normalized recurring ARR, adjust EBITDA for non-recurring billings, and implement customer success triage.",
        typical_severity_range="3 - 5",
    ),
    RiskCategory.INTEGRATION_COMPLEXITY: CategoryInfo(
        id="INTEGRATION_COMPLEXITY",
        name="Post-Deal Integration Complexity",
        description="Disparate enterprise software platforms (ERP/CRM), conflicting corporate cultures, geographically fragmented operations, and heavy integration friction.",
        signals=["integration challenge", "erp migration", "cultural conflict", "system incompatibility", "merger synergy delay", "post merger friction"],
        default_mitigation="Establish an active Integration Management Office (IMO), stage 100-day milestone execution roadmaps, and maintain parallel core ERP systems during migration.",
        typical_severity_range="3 - 4",
    ),
}
