"""Plain Text, Markdown, CSV, and SEC Filing Parser."""

import re
from typing import List
from app.core.security import sanitize_document_text
from app.domains.documents.parsers.base import ParsedChunk, ParsedDocument


class TextParser:
    """Extracts structured text from TXT, CSV, MD, and SEC text filings."""

    SECTION_PATTERN = re.compile(
        r"^(#{1,6}\s+.+|item\s+\d+[a-z]?[\.:]?|note\s+\d+[\.:\-]?|[A-Z0-9\s,\-]{4,60}:?$)",
        re.IGNORECASE | re.MULTILINE,
    )

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        """Parse raw text bytes into structured ParsedDocument."""
        text = file_bytes.decode("utf-8", errors="replace")
        text = sanitize_document_text(text)

        chunks: List[ParsedChunk] = []
        global_char_offset = 0
        chunk_idx = 0
        current_section = "General Document"

        # Split into paragraphs or blocks
        paragraphs = re.split(r"\n\s*\n", text)
        total_chars = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if this paragraph is a section heading
            if self.SECTION_PATTERN.match(para) and len(para) < 100:
                current_section = para.strip("# \t:-")
                continue

            total_chars += len(para)
            estimated_page = max(1, total_chars // 2500 + 1)
            char_start = global_char_offset
            char_end = char_start + len(para)

            chunks.append(
                ParsedChunk(
                    content=para,
                    page_number=estimated_page,
                    section_title=current_section,
                    chunk_index=chunk_idx,
                    token_count=len(para.split()),
                    char_offset_start=char_start,
                    char_offset_end=char_end,
                    source_type="PARAGRAPH",
                    metadata={"source_file": filename},
                )
            )
            chunk_idx += 1
            global_char_offset = char_end + 1

        estimated_pages = max(1, total_chars // 2500 + 1)

        return ParsedDocument(
            raw_text=text,
            page_count=estimated_pages,
            table_count=0,
            chunks=chunks,
            metadata={"filename": filename, "format": "TEXT"},
        )
