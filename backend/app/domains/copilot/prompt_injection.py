"""Prompt Injection Defense and Adversarial Input Sanitization Engine."""

import re
from typing import Tuple

ADVERSARIAL_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|system|prior)\s+(instructions|rules|prompts)", re.IGNORECASE),
    re.compile(r"reveal\s+(system\s+prompt|api\s+keys?|secrets?|passwords?|credentials?|internal\s+prompt)", re.IGNORECASE),
    re.compile(r"(show|print|output|display)\s+(the\s+)?(system\s+prompt|api\s+keys?|secrets?|passwords?|environment\s+variables)", re.IGNORECASE),
    re.compile(r"print\s+environment\s+variables", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are\s+now", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+dan\s+mode", re.IGNORECASE),
    re.compile(r"bypass\s+(all\s+)?(guardrails|safety\s+filters|security)", re.IGNORECASE),
    re.compile(r"repeat\s+the\s+(entire\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"purane\s+saare\s+instructions\s+bhool\s+jao", re.IGNORECASE),
    re.compile(r"api\s+key\s+(batao|dikhao|leak\s+karo)", re.IGNORECASE),
]


def sanitize_and_check_prompt_injection(user_prompt: str) -> Tuple[str, bool]:
    """Inspect user input for adversarial injection attempts.
    
    Returns:
        (sanitized_text, is_safe)
    """
    if not user_prompt:
        return "", True

    cleaned = user_prompt.strip()

    for pattern in ADVERSARIAL_PATTERNS:
        if pattern.search(cleaned):
            # Flagged as adversarial prompt injection attempt
            return cleaned, False

    return cleaned, True


def wrap_document_context_safely(document_chunks_text: str) -> str:
    """Enclose retrieved document context in strict passive boundaries to prevent indirect prompt injection."""
    return f"""
<UNTRUSTED_DOCUMENT_EVIDENCE_BOUNDARY>
{document_chunks_text}
</UNTRUSTED_DOCUMENT_EVIDENCE_BOUNDARY>
"""
