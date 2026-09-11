"""pypdf-based OCR engine — extracts native text from digital PDFs.

This is the primary engine for MetLife carátulas, which are all digital
(text-layer) PDFs.  Returns empty string if no text layer is found.
"""
from __future__ import annotations

import logging
from io import BytesIO

from .base import OcrEngine

_logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


class PypdfEngine(OcrEngine):
    """Engine that reads native PDF text via pypdf."""

    name = 'pypdf'

    def extraer_texto(self, pdf_bytes: bytes) -> str:
        if PdfReader is None:
            _logger.warning(
                'pypdf not installed — cannot extract text. '
                'Install with: pip install pypdf'
            )
            return ''

        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            paginas: list[str] = []
            for page in reader.pages:
                texto = page.extract_text()
                if texto:
                    paginas.append(texto)
            return '\n\n'.join(paginas)
        except Exception:
            _logger.exception('Error extracting text with pypdf')
            return ''
