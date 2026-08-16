"""Tests for Layout-Aware Document Chunker and Breadcrumb Hierarchy."""

import pytest
from app.domains.documents.chunker import LayoutAwareChunker
from app.domains.documents.parsers.base import ParsedChunk, ParsedDocument


def test_layout_aware_chunker_preserves_section_and_pages():
    """Verify chunker groups paragraphs under their respective section and tracks page numbers."""
    chunker = LayoutAwareChunker(target_chunk_tokens=100, max_chunk_tokens=200)

    parsed_doc = ParsedDocument(
        raw_text="Full text",
        page_count=2,
        table_count=1,
        chunks=[
            ParsedChunk(
                content="Paragraph 1 under Section A.",
                page_number=1,
                section_title="Section A: Diligence",
                chunk_index=0,
                token_count=10,
                char_offset_start=0,
                char_offset_end=30,
            ),
            ParsedChunk(
                content="Paragraph 2 under Section A with more details.",
                page_number=1,
                section_title="Section A: Diligence",
                chunk_index=1,
                token_count=12,
                char_offset_start=31,
                char_offset_end=80,
            ),
            ParsedChunk(
                content="Revenue Table: $45M in FY2023.",
                page_number=2,
                section_title="Section B: Financials",
                chunk_index=2,
                token_count=15,
                source_type="TABLE",
                char_offset_start=81,
                char_offset_end=120,
            ),
        ],
    )

    result_chunks = chunker.chunk_document(parsed_doc, "Diligence_Report.pdf")
    assert len(result_chunks) >= 2
    assert result_chunks[0].section_title == "Section A: Diligence"
    assert result_chunks[0].page_number == 1
    assert "Paragraph 1" in result_chunks[0].content
    assert "Paragraph 2" in result_chunks[0].content


def test_chunker_handles_empty_document():
    """Verify chunker handles empty documents gracefully."""
    chunker = LayoutAwareChunker()
    empty_doc = ParsedDocument(raw_text="", page_count=0, chunks=[])
    chunks = chunker.chunk_document(empty_doc, "empty.txt")
    assert len(chunks) == 0
