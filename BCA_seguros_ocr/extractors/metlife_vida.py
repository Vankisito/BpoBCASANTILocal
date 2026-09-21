"""MetLife Vida Individual carátula extractor.

Layout: VV-2-008 / IV-1-360 / IV6001 / IV1360 / IV1360ME — 2 pages.
All Vida products share the same layout; only product name varies.
Validated against 8 real PDFs with 100% accuracy.
"""

from __future__ import annotations

import contextlib
import re
from datetime import date

from .base import MESES_ES, ExtractorBase, extraer_fechas, normalizar_monto

# ---------------------------------------------------------------------------
# Regex patterns — COPIAR TAL CUAL del plan validado
# ---------------------------------------------------------------------------

# Contratante + Nº póliza: "Nombre del contratante\n PATRICIA LEAL CARREON  8497462"
_CONTRATANTE_LINE = r"Nombre del contratante\s*\n\s*([^\n]+)"

# Asegurado
_ASEGURADO = r"Nombre y domicilio del asegurado\s*\n([A-Z][A-Z ]+)"

# Producto: ANTES o DESPUÉS de "POLIZA DE SEGURO" (incluye acentos/mayúsculas latinas)
_LETRAS_MAY = r"A-Z\xC0-\xD6\xD8-\xDE"
_PRODUCTO_ANTES = rf"\n([{_LETRAS_MAY}][{_LETRAS_MAY} ]+?)\s+POLIZA DE SEGURO"
_PRODUCTO_DESPUES = rf"POLIZA DE SEGURO\s+([{_LETRAS_MAY}][{_LETRAS_MAY} ]+)"

# Agente
_AGENTE = r"AGENTE[- ]?\d+\s*:\s*(\d+)"

# Periodicidad
_PERIODICIDAD = r"PESOS\s+(ANUAL|MENSUAL|SEMESTRAL|TRIMESTRAL)"

# Forma de pago
_FORMA_PAGO = r"Forma de pago\s*\n\s*(.+?)(?:\n|$)"

# Prima anual total — línea "Recargo por pago ... Prima anual total <monto>"
# (layout VV-2-008 e IV1360); requiere IGNORECASE + DOTALL al buscar.
_PRIMA_ANUAL_RECARGO = (
    r"RECARGO POR PAGO\s*\n?\s*PRIMA ANUAL TOTAL\s*\n?\s*([\d,]+\.?\d*)"
)

# Prima anual total — layout IV1360ME: fila única con 4 montos
#   "67,303.79 1,300.00    68,603.79      68,603.79"
# el 3º es "prima anual total".
_PRIMA_ANUAL_ME = (
    r"Prima anual total\s*(?:de\s*\n?\s*coberturas)?.*?"
    r"\n\s*[\d,]+\.\d{2}\s+[\d,]+\.\d{2}\s+([\d,]+\.\d{2})"
    r"\s+[\d,]+\.\d{2}"
)

# Prima anual total — layout VV-2-008 (mayúsculas, fila directa)
_PRIMA_ANUAL_VV = r"PRIMA ANUAL TOTAL\s+([\d,]+\.?\d*)"

# Prima según forma de pago
_PRIMA_PAGO_RECARGO = (
    r"PRIMA SEG[ÚU]N\s*\n?\s*(?:FORMA DE\s*\n?\s*PAGO|Forma de pago)"
    r"\s*\n?\s*([\d,]+\.?\d*)"
)

# Recargo fijo
_RECARGO_VV = r"RECARGO FIJO\s+([\d,]+\.?\d*)"

# Suma asegurada
_SUMA_ASEGURADA = r"CUBIERTO\s+([\d,]+)"

# RFC
_RFC = r"R\.\s*F\.\s*C\.\s*:\s*(\w+)"

# Beneficiarios (página 2)
_BENEFICIARIOS = (
    r"([A-Z\xC0-\xD6\xD8-\xDE]"
    r"[A-Z\xC0-\xD6\xD8-\xDEa-z\xE0-\xF6\xF8-\xFF\s\.]+?)\s+"
    r"(Conyuge|Hijo|Hija|Madre|Padre|Hermana|Hermano)\s+(\d+)%"
)

# Fecha emisión: "Lugar y Fecha MEXICO, D.F. A 01 DE ABRIL DEL 2026"
_FECHA_EMISION_VV = r"A\s+(\d{1,2})\s+DE\s+(\w+)\s+DEL?\s+(\d{4})"

# Fecha emisión alternate: "Sucursal\n  111 30 03 2026"
_FECHA_EMISION_SUC = r"Sucursal\s*\n\s*\d+\s+(\d{2})\s+(\d{2})\s+(\d{4})"

# Beneficiario parentesco map
PARENTESCO_MAP_VIDA = {
    "Conyuge": "conyuge",
    "Hijo": "hijo",
    "Hija": "hijo",
    "Madre": "madre",
    "Padre": "padre",
    "Hermana": "hermano",
    "Hermano": "hermano",
}


class MetlifeVidaExtractor(ExtractorBase):
    """Extractor for MetLife Vida carátulas (VV-2-008 / IV-1-360)."""

    layout = "vida"

    def extract(self, texto: str) -> dict:
        """Extract all Vida fields from raw PDF text.

        Returns a dict with normalized values ready for Odoo.
        """
        data: dict = {}

        # --- Contratante + Nº póliza ---
        linea_contratante = self._search(_CONTRATANTE_LINE, texto)
        if linea_contratante:
            data["contratante_nombre"], data["poliza_numero"] = self._parse_contratante(
                linea_contratante
            )
        else:
            data["contratante_nombre"] = None
            data["poliza_numero"] = None

        # --- Asegurado ---
        data["asegurado_nombre"] = self._search(_ASEGURADO, texto)

        # --- Producto (try ANTES first, then DESPUÉS) ---
        data["producto_pdf"] = self._search(_PRODUCTO_ANTES, texto) or self._search(
            _PRODUCTO_DESPUES, texto
        )

        # --- Agente ---
        data["agente_clave"] = self._search(_AGENTE, texto)

        # --- Periodicidad ---
        periodicidad = self._search(_PERIODICIDAD, texto)
        data["periodicidad"] = periodicidad.lower() if periodicidad else "anual"
        data["forma_pago_pdf"] = self._search(_FORMA_PAGO, texto) or ""

        # --- Prima anual (según layout) ---
        # Layout VV/IV1360: "Recargo por pago ... Prima anual total <monto>"
        data["prima_anual"] = self._monto_desde(_PRIMA_ANUAL_RECARGO, texto)
        if not data["prima_anual"]:
            # Layout IV1360ME: fila con 4 montos, el 3º es la prima total
            data["prima_anual"] = self._monto_desde(_PRIMA_ANUAL_ME, texto)
        if not data["prima_anual"]:
            # Layout VV con fila simple en mayúsculas
            data["prima_anual"] = self._monto_desde(_PRIMA_ANUAL_VV, texto)
        data["prima_total"] = data["prima_anual"]

        # --- Prima según forma de pago ---
        data["prima_forma_pago"] = self._monto_desde(_PRIMA_PAGO_RECARGO, texto)
        if not data["prima_forma_pago"]:
            # Layout IV1360ME: misma fila, el 4º monto
            m = self._buscar_me_4to(texto)
            data["prima_forma_pago"] = normalizar_monto(m) if m else 0.0

        # --- Recargo fijo ---
        # 2º monto de la fila superior de coberturas (todos los layouts)
        recargo = self._recargo_fijo(texto)
        data["recargo_fijo"] = normalizar_monto(recargo) if recargo else 0.0

        # --- Suma asegurada ---
        data["suma_asegurada"] = self._to_float(self._search(_SUMA_ASEGURADA, texto))

        # --- RFC ---
        data["rfc"] = self._search(_RFC, texto)

        # --- Fechas ---
        data["fecha_emision"] = self._extract_fecha_emision(texto)
        data["fecha_inicio"], data["fecha_fin"] = self._extract_vigencia(
            texto, data["fecha_emision"]
        )

        # --- GMM-only fields (empty for Vida) ---
        data["prima_neta"] = 0.0
        data["iva"] = 0.0
        data["recargo_frac"] = 0.0
        data["deducible"] = 0.0
        data["coaseguro"] = 0.0
        data["plan"] = None
        data["nivel_hospitalario"] = None

        # --- Beneficiarios (página 2) ---
        data["beneficiarios"] = self._extract_beneficiarios(texto)
        data["num_beneficiarios"] = len(data["beneficiarios"])

        return data

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_contratante(linea: str) -> tuple[str | None, str | None]:
        """Parse ``NOMBRE COMPLETO  1234567`` → (nombre, poliza).

        Nº póliza Vida = 5-10 digits (sin ceros a la izquierda en el texto).
        """
        m = re.search(
            r"([A-Za-z\xC0-\xD6\xD8-\xDE\xE0-\xF6\xF8-\xFF ]+?)\s+" r"(\d{5,10})\s*$",
            linea.strip(),
        )
        if m:
            return m.group(1).strip(), m.group(2)
        # Fallback: whole line is the name
        return linea.strip(), None

    @staticmethod
    def _to_float(valor: str | None) -> float:
        if not valor:
            return 0.0
        return normalizar_monto(valor)

    @staticmethod
    def _monto_desde(pattern: str, texto: str) -> float:
        """Primer monto capturado por un patrón (IGNORECASE + DOTALL)."""
        m = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)
        return normalizar_monto(m.group(1)) if m else 0.0

    @staticmethod
    def _buscar_me_4to(texto: str) -> str | None:
        """IV1360ME: 4º monto de la fila única de primas (prima según forma de pago)."""
        m = re.search(
            r"forma de pago\s*\n\s*"
            r"[\d,]+\.\d{2}\s+[\d,]+\.\d{2}\s+[\d,]+\.\d{2}\s+([\d,]+\.\d{2})",
            texto,
            re.IGNORECASE | re.DOTALL,
        )
        return m.group(1) if m else None

    @staticmethod
    def _recargo_fijo(texto: str) -> str | None:
        """2º monto de la fila superior de coberturas (todos los layouts).

        Layout VV/IV1360:  "de coberturas\n   25,651.50   900.00       .00"
        Layout IV1360ME:  "67,303.79 1,300.00    68,603.79"
        """
        m = re.search(
            r"coberturas\s*\n\s*" r"[\d,]+\.\d{2}\s+([\d,]+\.\d{2})",
            texto,
            re.IGNORECASE | re.DOTALL,
        )
        return m.group(1) if m else None

    @staticmethod
    def _extract_fecha_emision(texto: str) -> str | None:
        """Try prose format first, then sucursal format."""

        # "A 01 DE ABRIL DEL 2026"
        m = re.search(_FECHA_EMISION_VV, texto, re.IGNORECASE)
        if m:
            dia = int(m.group(1))
            mes = MESES_ES.get(m.group(2).upper())
            anio = int(m.group(3))
            if mes:
                with contextlib.suppress(ValueError):
                    return date(anio, mes, dia).isoformat()

        # "Sucursal\n  111 30 03 2026"
        m = re.search(_FECHA_EMISION_SUC, texto)
        if m:
            with contextlib.suppress(ValueError):
                return date(
                    int(m.group(3)), int(m.group(2)), int(m.group(1))
                ).isoformat()

        return None

    @staticmethod
    def _extract_vigencia(
        texto: str, fecha_emision: str | None
    ) -> tuple[str | None, str | None]:
        """Infer Vida validity from dates printed in the coverage table."""
        fechas = extraer_fechas(texto)
        if not fechas:
            return None, None
        emision = date.fromisoformat(fecha_emision) if fecha_emision else None
        posteriores = [fecha for fecha in fechas if not emision or fecha > emision]
        if not posteriores:
            return None, None
        fecha_fin = max(posteriores)
        inicios = [
            fecha
            for fecha in fechas
            if fecha < fecha_fin and (not emision or fecha.year == emision.year)
        ]
        if not inicios:
            return None, None
        return max(inicios).isoformat(), fecha_fin.isoformat()

    @staticmethod
    def _extract_beneficiarios(texto: str) -> list[dict]:
        """Extract beneficiaries from page 2 table.

        Returns list of dicts with 'nombre', 'parentesco', 'porcentaje'.
        """
        result: list[dict] = []
        for m in re.finditer(_BENEFICIARIOS, texto):
            parentesco_raw = m.group(2)
            parentesco = PARENTESCO_MAP_VIDA.get(parentesco_raw, "otro")
            result.append(
                {
                    "nombre": m.group(1).strip(),
                    "parentesco": parentesco,
                    "porcentaje": float(m.group(3)),
                }
            )
        return result
