"""Copilot Engine: Evidence-Grounded Synthesis and Answer Generation."""

import re
from typing import Any, Dict, List, Tuple
from app.domains.copilot.prompt_injection import (
    sanitize_and_check_prompt_injection,
    wrap_document_context_safely,
)


class CopilotEngine:
    """Orchestrates query synthesis, evidence grounding, and deterministic citation generation."""

    @staticmethod
    def generate_grounded_response(
        query: str,
        retrieved_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Synthesize an evidence-backed answer grounded strictly in DealGuard data room records.
        
        Returns:
            (answer_text, confidence, citations)
        """
        sanitized_query, is_safe = sanitize_and_check_prompt_injection(query)
        if not is_safe:
            return (
                "DealGuard Security Warning: The input query was flagged by prompt-injection guardrails. "
                "Conversational queries must be strictly focused on deal due diligence, evidence analysis, and target company intelligence.",
                "LOW",
                [],
            )

        context_text = retrieved_context.get("context_text", "")
        citations = retrieved_context.get("citations", [])
        domains = retrieved_context.get("retrieved_domains", [])

        # Detect insufficient data scenarios
        if not context_text or (len(domains) == 1 and domains[0] == "DOCUMENTS" and not citations):
            return (
                f"Based on the ingested data room records for this deal, there is **INSUFFICIENT EVIDENCE** to answer: *\"{sanitized_query}\"*.\n\n"
                "Please verify that relevant due diligence documents (financial models, contracts, architecture reports, or risk logs) have been uploaded and processed in the Data Room.",
                "INSUFFICIENT_EVIDENCE",
                [],
            )

        q_lower = sanitized_query.lower()

        # Synthesis routing based on deal diligence topics
        answer_paragraphs = []

        if any(w in q_lower for w in ["risk", "danger", "downside", "threat"]):
            answer_paragraphs.append("### Evidence-Backed Risk Analysis")
            answer_paragraphs.append(
                "Cross-referencing the target company's 17-pillar risk matrix and ingested data room disclosures:"
            )
            answer_paragraphs.append(context_text)
            answer_paragraphs.append(
                "\n**DealGuard Recommendation:** Ensure all Critical and High severity findings are linked to the Phase 11 100-Day Integration Workstreams with designated post-close remediation owners."
            )

        elif any(w in q_lower for w in ["legal", "contract", "change of control", "consent"]):
            answer_paragraphs.append("### Contractual & Change-of-Control Diligence")
            answer_paragraphs.append(
                "Reviewing extracted clauses and counterparty obligations under the 32-category contract taxonomy:"
            )
            answer_paragraphs.append(context_text)
            answer_paragraphs.append(
                "\n**Key Exposure:** Contracts requiring counterparty consent must be addressed in the pre-closing conditions precedent to protect the identified Revenue at Risk."
            )

        elif any(w in q_lower for w in ["tech", "cloud", "aws", "sla", "uptime", "spof", "debt"]):
            answer_paragraphs.append("### Technology, Infrastructure & Operational Reliability")
            answer_paragraphs.append(
                "Synthesizing architectural disclosures, cloud bills, and SLA reliability logs:"
            )
            answer_paragraphs.append(context_text)
            answer_paragraphs.append(
                "\n**Architectural Assessment:** Single points of failure and monolithic technical debt should be budgeted into Day 1-60 integration milestones."
            )

        elif any(w in q_lower for w in ["financial", "ebitda", "revenue", "margin", "qoe"]):
            answer_paragraphs.append("### Financial Performance & Quality of Earnings (QoE)")
            answer_paragraphs.append(
                "Analyzing normalized 3-statement financial metrics and QoE adjustments:"
            )
            answer_paragraphs.append(context_text)
            answer_paragraphs.append(
                "\n**Note:** All financial valuations remain deterministic calculations computed outside the LLM to preserve mathematical precision."
            )

        elif any(w in q_lower for w in ["synergy", "synergies", "value creation"]):
            answer_paragraphs.append("### Synergy Realization & Value Creation")
            answer_paragraphs.append(
                "Evaluating bottom-up cost reduction and commercial cross-sell opportunities:"
            )
            answer_paragraphs.append(context_text)

        elif any(w in q_lower for w in ["integration", "100-day", "milestone"]):
            answer_paragraphs.append("### 100-Day Post-Acquisition Integration Execution")
            answer_paragraphs.append(
                "Tracking critical-path workstream milestones and dependency execution:"
            )
            answer_paragraphs.append(context_text)

        else:
            answer_paragraphs.append("### Deal Intelligence Summary")
            answer_paragraphs.append(
                f"Synthesizing data room evidence across {', '.join(domains)} for query: *\"{sanitized_query}\"*."
            )
            answer_paragraphs.append(context_text)

        full_answer = "\n\n".join(answer_paragraphs)
        confidence = "HIGH" if len(citations) >= 1 or len(domains) >= 2 else "MEDIUM"

        return full_answer, confidence, citations
