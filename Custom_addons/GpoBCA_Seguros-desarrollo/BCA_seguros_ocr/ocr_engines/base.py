"""OCR engine abstraction layer.

Each engine implements ``extraer_texto`` to convert PDF bytes into a plain
text string.  The staging model delegates to the engine selected at
configuration time; for the MVP, ``PypdfEngine`` is the only implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class OcrEngine(ABC):
    """Base class for OCR engines."""

    name: str = "base"

    @abstractmethod
    def extraer_texto(self, pdf_bytes: bytes) -> str:
        """Extract plain text from PDF binary content.

        Returns empty string if the engine cannot extract text (e.g. scanned
        PDF without a text layer).
        """
        ...
