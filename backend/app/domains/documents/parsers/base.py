"""Parsed Document and Chunk Data Transfer Objects for Layout-Aware Ingestion."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParsedChunk:
    """Extracted text chunk with explicit structural breadcrumbs and source locations."""
    content: str
    page_number: int = 1
    section_title: Optional[str] = None
    chunk_index: int = 0
    token_count: int = 0
    char_offset_start: Optional[int] = None
    char_offset_end: Optional[int] = None
    source_type: str = "PARAGRAPH"  # PARAGRAPH, TABLE, HEADING, LIST_ITEM
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Complete structured extraction result from a document."""
    raw_text: str
    page_count: int = 1
    table_count: int = 0
    chunks: List[ParsedChunk] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
