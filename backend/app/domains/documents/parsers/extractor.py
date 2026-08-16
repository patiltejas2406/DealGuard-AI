"""Unified Document Extractor Registry for Multi-Format Ingestion."""

import os
from typing import Dict
from app.core.exceptions import ValidationException
from app.domains.documents.parsers.base import ParsedDocument
from app.domains.documents.parsers.docx_parser import DocxParser
from app.domains.documents.parsers.pdf_parser import PDFParser
from app.domains.documents.parsers.text_parser import TextParser
from app.domains.documents.parsers.xlsx_parser import XlsxParser


class DocumentExtractorRegistry:
    """Routes document bytes to format-specific layout-aware parsers."""

    def __init__(self) -> None:
        self.pdf_parser = PDFParser()
        self.docx_parser = DocxParser()
        self.xlsx_parser = XlsxParser()
        self.text_parser = TextParser()

    async def extract(self, file_bytes: bytes, filename: str, mime_type: str = "") -> ParsedDocument:
        """Parse document bytes based on file extension and MIME type."""
        ext = os.path.splitext(filename)[1].lower().lstrip(".")

        if ext == "pdf" or "pdf" in mime_type.lower():
            return await self.pdf_parser.parse(file_bytes, filename)
        elif ext in ["docx", "doc"] or "wordprocessingml" in mime_type.lower():
            return await self.docx_parser.parse(file_bytes, filename)
        elif ext in ["xlsx", "xls", "xlsm"] or "spreadsheetml" in mime_type.lower():
            return await self.xlsx_parser.parse(file_bytes, filename)
        elif ext in ["txt", "csv", "md", "json", "html", "htm"] or "text" in mime_type.lower():
            return await self.text_parser.parse(file_bytes, filename)
        else:
            raise ValidationException(
                f"Unsupported document format: '.{ext}'. Supported formats: PDF, DOCX, XLSX, TXT, CSV, MD, JSON, HTML."
            )
