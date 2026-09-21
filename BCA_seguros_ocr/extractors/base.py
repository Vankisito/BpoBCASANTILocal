"""Extractor base and shared utilities for MetLife carátula parsing.

Provides:
- ``detectar_layout()`` — classifies text as GMM / Vida / desconocido
- ``normalizar_monto()`` — converts "1,234.56" → float
- ``normalizar_fecha_ocr()`` — converts various date formats → date
- ``MESES_ES`` — Spanish month name → number mapping
- ``ExtractorBase`` — common regex helpers
"""

from __future__ import annotations

import contextlib
import logging
import re
from datetime import date, datetime

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Layout detection
# ---------------------------------------------------------------------------
_GMM_MARKERS = ("GO-2-025", "GASTOS MEDICOS")
_VIDA_MARKERS = ("VV-2-008", "IV-1-360", "VIDA INDIVIDUAL")


def detectar_layout(texto: str) -> str:
    """Detect whether the text corresponds to GMM or Vida layout.

    Returns 'gmm', 'vida', or 'desconocido'.
    """
    texto_upper = texto.upper()
    for marker in _GMM_MARKERS:
        if marker in texto:
            return "gmm"
    for marker in _VIDA_MARKERS:
        if marker in texto:
            return "vida"
    # Fallback: search in upper-cased text for partial matches
    if "GASTOS MEDICOS" in texto_upper:
        return "gmm"
    if "VIDA INDIVIDUAL" in texto_upper:
        return "vida"
    return "desconocido"


# ---------------------------------------------------------------------------
# Numeric / date helpers
# ---------------------------------------------------------------------------
def normalizar_monto(valor) -> float:
    """Convert ``"1,234.56"`` / ``1234.56`` / ``"$1,234"`` → ``float``.

    Empty / None → 0.0.  Raises ``ValueError`` on invalid input.
    """
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace(",", "").replace("$", "").replace("%", "")
    if not texto:
        return 0.0
    return float(texto)


MESES_ES = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SEPTIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12,
}


def normalizar_fecha_ocr(texto: str) -> date | None:
    """Try multiple date formats commonly found in MetLife carátulas.

    Formats tried:
    - DD/MM/YYYY, DD-MM-YYYY
    - YYYY-MM-DD
    - ``A DD DE MES DE YYYY`` (Spanish prose)
    - DD MM YYYY (space-separated)
    - ``DD MES AAAA`` (Spanish month name)
    """
    if not texto or not texto.strip():
        return None
    texto = texto.strip()

    # Spanish prose: "A 01  DE  ABRIL  DE  2026"
    m = re.search(
        r"A\s+(\d{1,2})\s+DE\s+(\w+)\s+DE\s+(\d{4})",
        texto,
        re.IGNORECASE,
    )
    if m:
        dia, mes_name, anio = int(m.group(1)), m.group(2).upper(), int(m.group(3))
        mes = MESES_ES.get(mes_name)
        if mes:
            with contextlib.suppress(ValueError):
                return date(anio, mes, dia)

    # Standard formats
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %m %Y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue

    # "DD MES AAAA" — e.g. "30 03 2026"
    m = re.match(r"(\d{1,2})\s+(\d{1,2})\s+(\d{4})", texto)
    if m:
        with contextlib.suppress(ValueError):
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    return None


def extraer_fechas(texto: str) -> list[date]:
    """Extract slash- or space-separated dates from OCR text."""
    fechas = []
    for patron in (
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        r"(\d{1,2})\s+(\d{1,2})\s+(\d{4})",
    ):
        for match in re.finditer(patron, texto):
            try:
                valor = date(
                    int(match.group(3)),
                    int(match.group(2)),
                    int(match.group(1)),
                )
            except ValueError:
                continue
            if valor not in fechas:
                fechas.append(valor)
    return fechas


# ---------------------------------------------------------------------------
# Base extractor
# ---------------------------------------------------------------------------
class ExtractorBase:
    """Base class for layout-specific extractors."""

    layout: str = "desconocido"

    def extract(self, texto: str) -> dict:
        """Extract fields from text.  Subclasses must implement."""
        raise NotImplementedError

    @staticmethod
    def _search(pattern: str, texto: str, flags: int = 0) -> str | None:
        """Safe regex search — returns first group or None."""
        m = re.search(pattern, texto, flags)
        return m.group(1).strip() if m else None

    @staticmethod
    def _search_all(pattern: str, texto: str, flags: int = 0) -> list[re.Match]:
        """Return all matches."""
        return list(re.finditer(pattern, texto, flags))
