"""Unit tests for MetLife carátula extractors.

Tests run against golden data from 10 real PDFs (2 GMM + 8 Vida).
Fixtures are the raw text extracted by pypdf — tests validate the regex
parsers WITHOUT requiring pypdf at runtime. Run via Odoo test runner:

    odoo --test-enable --test-tags '/BCA_seguros_ocr'
"""

from __future__ import annotations

import os
from unittest import SkipTest

from odoo.tests.common import TransactionCase

from ..extractors.base import detectar_layout, normalizar_monto
from ..extractors.metlife_gmm import MetlifeGmmExtractor
from ..extractors.metlife_vida import MetlifeVidaExtractor

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(poliza: str) -> str:
    """Load text fixture by póliza number (tolerates `000` prefixes)."""
    if not os.path.exists(FIXTURES_DIR):
        raise SkipTest(f"Fixtures dir missing: {FIXTURES_DIR}")
    # Fixture cuyo nombre empiece por la póliza (tolerando ceros a la izquierda)
    basename = poliza.lstrip("0")
    candidates = [
        f
        for f in os.listdir(FIXTURES_DIR)
        if f.startswith("000") and f.lstrip("0").startswith(basename)
    ] or [f for f in os.listdir(FIXTURES_DIR) if f.startswith(poliza)]
    if not candidates:
        raise SkipTest(f"Fixture not found for póliza: {poliza}")
    path = os.path.join(FIXTURES_DIR, sorted(candidates)[0])
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Golden data — source of truth for validation
# ---------------------------------------------------------------------------
GMM_GOLDEN = {
    "0001420597": {
        "poliza_numero": "0001420597",
        "contratante_nombre": "JOSEMILIO RAMOS LOPEZ",
        "producto_pdf": "GASTOS MEDICOS MEDICALIFE FAM.",
        "agente_clave": "074887",
        "periodicidad": "semestral",
        "prima_total": 54119.62,
        "prima_neta": 43418.12,
        "iva": 7464.78,
        "recargo_frac": 1736.72,
        "deducible": 52000.0,
        "coaseguro": 0.10,
    },
    "0000018128": {
        "poliza_numero": "0000018128",
        "contratante_nombre": "JORGE ALEJANDRO ALVAREZ ZAVALZA",
        "producto_pdf": "PRIMORDIAL",
        "agente_clave": "073753",
        "periodicidad": "mensual",
        "prima_total": 4617.68,
        "prima_neta": 3600.0,
        "iva": 636.88,
        "recargo_frac": 280.80,
    },
}

VIDA_GOLDEN = {
    "8497462": {
        "poliza_numero": "8497462",
        "contratante_nombre": "PATRICIA LEAL CARREON",
        "producto_pdf": "TEMPOLIFE",
        "agente_clave": "74570",
        "periodicidad": "anual",
        "prima_anual": 26551.50,
        "prima_forma_pago": 26551.50,
        "recargo_fijo": 900.0,
        "suma_asegurada": 100000.0,
        "rfc": "LECP6607118I1",
        "num_beneficiarios": 3,
    },
    "8495803": {
        "poliza_numero": "8495803",
        "contratante_nombre": "VERONICA MARIA MARTINEZ MENDEZ",
        "producto_pdf": "FLEXI LIFE INVERSION",
        "agente_clave": "73110",
        "periodicidad": "anual",
        "prima_anual": 445.90,
        "suma_asegurada": 0.0,
        "num_beneficiarios": 2,
    },
    "8493880": {
        "poliza_numero": "8493880",
        "contratante_nombre": "RUTH LOPEZ SALAZAR",
        "producto_pdf": "METALIFE MUJER",
        "agente_clave": "74845",
        "periodicidad": "anual",
        "prima_anual": 66999.98,
        "suma_asegurada": 2232685.0,
        "num_beneficiarios": 1,
    },
    "8497494": {
        "poliza_numero": "8497494",
        "contratante_nombre": "ANA LILIA SANCHEZ QUIROZ",
        "producto_pdf": "TOTALIFE",
        "agente_clave": "73801",
        "periodicidad": "anual",
        "prima_anual": 54326.0,
        "suma_asegurada": 0.0,
        "num_beneficiarios": 2,
    },
    "8494374": {
        "poliza_numero": "8494374",
        "contratante_nombre": "MOISES PEREYRA MENESES",
        "producto_pdf": "VIDA INDIVIDUAL",
        "agente_clave": "74511",
        "periodicidad": "mensual",
        "prima_anual": 42963.96,
        "suma_asegurada": 780000.0,
        "num_beneficiarios": 1,
    },
    "8496336": {
        "poliza_numero": "8496336",
        "contratante_nombre": "JOSE PABLO TORRES MENDOZA",
        "producto_pdf": "METALIFE EDUCACIÓN",
        "agente_clave": "73801",
        "periodicidad": "anual",
        "prima_anual": 68603.79,
        "suma_asegurada": 2145755.0,
        "num_beneficiarios": 1,
    },
    "8497472": {
        "poliza_numero": "8497472",
        "contratante_nombre": "MARIANNE HUGUES BARRAGAN",
        "producto_pdf": "METALIFE RETIRO",
        "agente_clave": "73753",
        "periodicidad": "mensual",
        "prima_anual": 24587.39,
        "suma_asegurada": 1026850.0,
        "num_beneficiarios": 3,
    },
    "8495582": {
        "poliza_numero": "8495582",
        "contratante_nombre": "DEFENIX CARTONES SA DE CV",
        "producto_pdf": "METALIFE TU FUTURO",
        "agente_clave": "74001",
        "periodicidad": "mensual",
        "prima_anual": 22800.0,
        "suma_asegurada": 0.0,
        "num_beneficiarios": 1,
    },
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestLayoutDetection(TransactionCase):
    """Test layout detection from text markers."""

    def test_gmm_marker_go(self):
        self.assertEqual(detectar_layout("GO-2-025 VER. 2"), "gmm")

    def test_gmm_marker_medical(self):
        self.assertEqual(
            detectar_layout("Póliza de Seguro de:\nGASTOS MEDICOS MEDICALIFE"), "gmm"
        )

    def test_vida_marker_vv(self):
        self.assertEqual(detectar_layout("VV-2-008\nTEMPOLIFE"), "vida")

    def test_vida_marker_iv(self):
        self.assertEqual(detectar_layout("IV-1-360\nPOLIZA DE SEGURO"), "vida")

    def test_vida_marker_individual(self):
        self.assertEqual(
            detectar_layout("TEMPOLIFE POLIZA DE SEGURO VIDA INDIVIDUAL"), "vida"
        )

    def test_unknown(self):
        self.assertEqual(detectar_layout("random text without markers"), "desconocido")


class TestNormalizarMonto(TransactionCase):
    """Test monetary value normalization."""

    def test_comma_separated(self):
        self.assertAlmostEqual(normalizar_monto("43,418.12"), 43418.12, places=2)

    def test_plain_number(self):
        self.assertAlmostEqual(normalizar_monto("4617.68"), 4617.68, places=2)

    def test_with_dollar(self):
        self.assertAlmostEqual(normalizar_monto("$1,500.00"), 1500.00, places=2)

    def test_integer(self):
        self.assertAlmostEqual(normalizar_monto(100000), 100000.0, places=2)

    def test_empty(self):
        self.assertAlmostEqual(normalizar_monto(""), 0.0, places=2)

    def test_none(self):
        self.assertAlmostEqual(normalizar_monto(None), 0.0, places=2)


class TestGmmExtractor(TransactionCase):
    """Test GMM extractor against golden data (fixture-dependent)."""

    def setUp(self):
        self.extractor = MetlifeGmmExtractor()

    def _extract_and_compare(self, fixture_name: str, golden: dict):
        texto = _load_fixture(fixture_name)
        data = self.extractor.extract(texto)
        for key, expected in golden.items():
            actual = data.get(key)
            if isinstance(expected, float):
                self.assertAlmostEqual(
                    actual,
                    expected,
                    places=2,
                    msg=f"{fixture_name}: {key} expected {expected}, got {actual}",
                )
            else:
                self.assertEqual(
                    actual,
                    expected,
                    msg=f"{fixture_name}: {key} expected {expected!r}, got {actual!r}",
                )

    def test_0001420597(self):
        self._extract_and_compare("0001420597", GMM_GOLDEN["0001420597"])

    def test_0000018128(self):
        self._extract_and_compare("0000018128", GMM_GOLDEN["0000018128"])


class TestVidaExtractor(TransactionCase):
    """Test Vida extractor against golden data (fixture-dependent)."""

    def setUp(self):
        self.extractor = MetlifeVidaExtractor()

    def _extract_and_compare(self, fixture_name: str, golden: dict):
        texto = _load_fixture(fixture_name)
        data = self.extractor.extract(texto)
        for key, expected in golden.items():
            actual = data.get(key)
            if isinstance(expected, float):
                self.assertAlmostEqual(
                    actual,
                    expected,
                    places=2,
                    msg=f"{fixture_name}: {key} expected {expected}, got {actual}",
                )
            else:
                self.assertEqual(
                    actual,
                    expected,
                    msg=f"{fixture_name}: {key} expected {expected!r}, got {actual!r}",
                )

    def test_8497462_tempolife(self):
        self._extract_and_compare("8497462", VIDA_GOLDEN["8497462"])

    def test_8495803_flexi(self):
        self._extract_and_compare("8495803", VIDA_GOLDEN["8495803"])

    def test_8493880_metalife_mujer(self):
        self._extract_and_compare("8493880", VIDA_GOLDEN["8493880"])

    def test_8497494_totalife(self):
        self._extract_and_compare("8497494", VIDA_GOLDEN["8497494"])

    def test_8494374_vida_individual(self):
        self._extract_and_compare("8494374", VIDA_GOLDEN["8494374"])

    def test_8496336_educacion(self):
        self._extract_and_compare("8496336", VIDA_GOLDEN["8496336"])

    def test_8497472_retiro(self):
        self._extract_and_compare("8497472", VIDA_GOLDEN["8497472"])

    def test_8495582_tu_futuro(self):
        self._extract_and_compare("8495582", VIDA_GOLDEN["8495582"])
