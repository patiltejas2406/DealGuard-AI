"""PDF Document Parser with Page-Aware Extraction and Heading Hierarchy Detection."""

import io
import re
from typing import List, Optional
from pypdf import PdfReader
from app.core.security import sanitize_document_text
from app.domains.documents.parsers.base import ParsedChunk, ParsedDocument


class PDFParser:
    """Extracts structured text, tables, and page metadata from PDF documents."""

    HEADING_PATTERN = re.compile(
        r"^(item\s+\d+[a-z]?[\.:]?|note\s+\d+[\.:\-]?|section\s+\d+[\.:\-]?|[A-Z0-9\s,\-]{4,60}:?$)",
        re.IGNORECASE,
    )

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        """Parse raw PDF bytes into a structured ParsedDocument with page breadcrumbs."""
        stream = io.BytesIO(file_bytes)
        reader = PdfReader(stream)
        page_count = len(reader.pages)

        chunks: List[ParsedChunk] = []
        full_text_parts: List[str] = []
        global_char_offset = 0
        chunk_idx = 0
        current_section = "Overview"

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            page_text = page.extract_text() or ""
            page_text = sanitize_document_text(page_text)

            if not page_text.strip():
                continue

            full_text_parts.append(page_text)
            lines = [l.strip() for l in page_text.splitlines() if l.strip()]

            current_paragraph: List[str] = []

            for line in lines:
                # Check for section/heading match
                if self.HEADING_PATTERN.match(line) and len(line) < 80:
                    # Flush existing paragraph
                    if current_paragraph:
                        para_text = " ".join(current_paragraph)
                        char_start = global_char_offset
                        char_end = char_start + len(para_text)
                        chunks.append(
                            ParsedChunk(
                                content=para_text,
                                page_number=page_num,
                                section_title=current_section,
                                chunk_index=chunk_idx,
                                token_count=len(para_text.split()),
                                char_offset_start=char_start,
                                char_offset_end=char_end,
                                source_type="PARAGRAPH",
                                metadata={"page": page_num, "source_file": filename},
                            )
                        )
                        chunk_idx += 1
                        global_char_offset = char_end + 1
                        current_paragraph = []

                    current_section = line.strip(" :-\t")
                    # Also emit heading as a breadcrumb chunk if informative
                    continue

                current_paragraph.append(line)

            if current_paragraph:
                para_text = " ".join(current_paragraph)
                char_start = global_char_offset
                char_end = char_start + len(para_text)
                chunks.append(
                    ParsedChunk(
                        content=para_text,
                        page_number=page_num,
                        section_title=current_section,
                        chunk_index=chunk_idx,
                        token_count=len(para_text.split()),
                        char_offset_start=char_start,
                        char_offset_end=char_end,
                        source_type="PARAGRAPH",
                        metadata={"page": page_num, "source_file": filename},
                    )
                )
                chunk_idx += 1
                global_char_offset = char_end + 1

        raw_text = "\n\n".join(full_text_parts)
        return ParsedDocument(
            raw_text=raw_text,
            page_count=page_count,
            table_count=0,
            chunks=chunks,
            metadata={"filename": filename, "format": "PDF", "page_count": page_count},
        )
