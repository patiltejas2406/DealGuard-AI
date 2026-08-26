"""Server-Sent Events (SSE) Streaming Generator for Grounded Copilot Responses."""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List


async def generate_sse_copilot_stream(
    answer_text: str,
    confidence: str,
    citations: List[Dict[str, Any]],
    retrieved_domains: List[str],
) -> AsyncGenerator[str, None]:
    """Stream response tokens and citations over Server-Sent Events (SSE) protocol."""
    # 1. Send domain badges
    for domain in retrieved_domains:
        payload = {"event": "domain", "data": domain}
        yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(0.01)

    # 2. Stream tokens (words/chunks) progressively
    words = answer_text.split(" ")
    buffer = []
    for idx, word in enumerate(words):
        buffer.append(word)
        if len(buffer) >= 3 or idx == len(words) - 1:
            chunk = " ".join(buffer) + (" " if idx < len(words) - 1 else "")
            payload = {"event": "token", "data": chunk}
            yield f"data: {json.dumps(payload)}\n\n"
            buffer = []
            await asyncio.sleep(0.015)

    # 3. Stream grounded citations
    for cit in citations:
        payload = {"event": "citation", "data": cit}
        yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(0.01)

    # 4. Stream completion event
    done_payload = {
        "event": "done",
        "data": {
            "confidence": confidence,
            "citations_count": len(citations),
            "domains_count": len(retrieved_domains),
        },
    }
    yield f"data: {json.dumps(done_payload)}\n\n"
