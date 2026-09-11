"""pypdf-based OCR engine — extracts native text from digital PDFs.

This is the primary engine for MetLife carátulas, which are all digital
(text-layer) PDFs.  Returns empty string if no text layer is found.

Raises typed exceptions so the caller can show user-friendly errors for
corrupt, invalid, or password-protected files instead of raw traces.
"""

from __future__ import annotations

import logging
from io import BytesIO

from .base import OcrEngine

_logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
    from pypdf.errors import FileNotDecryptedError, PdfReadError
except ImportError:
    PdfReader = None
    FileNotDecryptedError = PdfReadError = Exception


class PdfInvalidoError(Exception):
    """File is not a valid/corrupt PDF (or not a PDF at all)."""


class PdfEncriptadoError(Exception):
    """PDF is password-protected and cannot be read."""


class PypdfEngine(OcrEngine):
    """Engine that reads native PDF text via pypdf."""

    name = "pypdf"

    def extraer_texto(self, pdf_bytes: bytes) -> str:
        if PdfReader is None:
            _logger.warning(
                "pypdf not installed — cannot extract text. "
                "Install with: pip install pypdf"
            )
            return ""

        try:
            reader = PdfReader(BytesIO(pdf_bytes))
        except FileNotDecryptedError as exc:
            raise PdfEncriptadoError from exc
        except Exception as exc:
            _logger.exception("Error opening PDF with pypdf")
            raise PdfInvalidoError from exc

        try:
            paginas: list[str] = []
            for page in reader.pages:
                texto = page.extract_text()
                if texto:
                    paginas.append(texto)
            return "\n\n".join(paginas)
        except FileNotDecryptedError as exc:
            raise PdfEncriptadoError from exc
        except Exception:
            _logger.exception("Error extracting text with pypdf")
            return ""
