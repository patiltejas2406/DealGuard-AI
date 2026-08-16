"""Layout-Aware Document Chunker with Section Hierarchy & Evidence Grounding."""

from typing import List, Optional
from app.domains.documents.parsers.base import ParsedChunk, ParsedDocument


class LayoutAwareChunker:
    """
    Intelligently splits and combines parsed document blocks into optimal RAG chunks
    while preserving page numbers, section headers, and character-level coordinates.
    """

    def __init__(self, target_chunk_tokens: int = 500, max_chunk_tokens: int = 800, overlap_tokens: int = 50) -> None:
        self.target_chunk_tokens = target_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_document(self, parsed_doc: ParsedDocument, doc_name: str) -> List[ParsedChunk]:
        """Convert parsed document elements into standardized, citation-ready RAG chunks."""
        if not parsed_doc.chunks:
            # Fallback if raw text exists but no granular chunks
            words = parsed_doc.raw_text.split()
            if not words:
                return []
            return [
                ParsedChunk(
                    content=parsed_doc.raw_text,
                    page_number=1,
                    section_title="Full Document",
                    chunk_index=0,
                    token_count=len(words),
                    char_offset_start=0,
                    char_offset_end=len(parsed_doc.raw_text),
                    source_type="PARAGRAPH",
                    metadata={"source_file": doc_name},
                )
            ]

        final_chunks: List[ParsedChunk] = []
        chunk_idx = 0

        current_text_blocks: List[str] = []
        current_token_count = 0
        current_page = parsed_doc.chunks[0].page_number
        current_section = parsed_doc.chunks[0].section_title or "General"
        current_source_type = parsed_doc.chunks[0].source_type
        current_char_start: Optional[int] = parsed_doc.chunks[0].char_offset_start
        last_char_end: Optional[int] = parsed_doc.chunks[0].char_offset_end

        for element in parsed_doc.chunks:
            element_tokens = element.token_count or len(element.content.split())

            # If element is a self-contained large table or large block, or section changes significantly
            is_large_table = element.source_type == "TABLE" and element_tokens > 200
            section_changed = element.section_title and element.section_title != current_section

            if (current_token_count + element_tokens > self.max_chunk_tokens) or is_large_table or section_changed:
                if current_text_blocks:
                    combined_content = "\n\n".join(current_text_blocks)
                    final_chunks.append(
                        ParsedChunk(
                            content=combined_content,
                            page_number=current_page,
                            section_title=current_section,
                            chunk_index=chunk_idx,
                            token_count=current_token_count,
                            char_offset_start=current_char_start or 0,
                            char_offset_end=last_char_end or len(combined_content),
                            source_type=current_source_type,
                            metadata={"document_name": doc_name, "section": current_section},
                        )
                    )
                    chunk_idx += 1
                    current_text_blocks = []
                    current_token_count = 0

            # Start new block or add to current
            if not current_text_blocks:
                current_page = element.page_number
                current_section = element.section_title or "General"
                current_source_type = element.source_type
                current_char_start = element.char_offset_start

            current_text_blocks.append(element.content)
            current_token_count += element_tokens
            last_char_end = element.char_offset_end

        # Flush trailing block
        if current_text_blocks:
            combined_content = "\n\n".join(current_text_blocks)
            final_chunks.append(
                ParsedChunk(
                    content=combined_content,
                    page_number=current_page,
                    section_title=current_section,
                    chunk_index=chunk_idx,
                    token_count=current_token_count,
                    char_offset_start=current_char_start or 0,
                    char_offset_end=last_char_end or len(combined_content),
                    source_type=current_source_type,
                    metadata={"document_name": doc_name, "section": current_section},
                )
            )

        return final_chunks
