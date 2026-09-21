"""Unit tests for OCR → Odoo resolver helpers.

Validates `resolver_producto`:
- canonical MetLife rules (ported from the Convertidor BCA) that run before
  fuzzy matching and encode the semantic equivalences BCA confirmed
  (e.g. ``METALIFE EDUCACION`` → ``Metlife Educalife``).
 - fuzzy word matching fallback: case/accent-insensitive word matching,
   hard ramo filtering, and ambiguity warnings.

Fixtures mirror the real MetLife catalog present in the client DB.

Run via Odoo test runner:

    odoo --test-enable --test-tags '/BCA_seguros_ocr'
"""

from __future__ import annotations

import os

from odoo.tests.common import TransactionCase

from ..extractors.metlife_gmm import MetlifeGmmExtractor
from ..extractors.metlife_vida import MetlifeVidaExtractor
from ..helpers import _normalizar_nombre, mapear_producto_metlife, resolver_producto


class TestNormalizarNombre(TransactionCase):
    """Tokenize + normalize OCR/product names."""

    def test_mayusculas_y_minusculas(self):
        self.assertEqual(
            _normalizar_nombre("Metlife Primordial"),
            ["metlife", "primordial"],
        )

    def test_ocr_mayusculas(self):
        self.assertEqual(_normalizar_nombre("PRIMORDIAL"), ["primordial"])

    def test_acentos_eliminados(self):
        self.assertEqual(
            _normalizar_nombre("METALIFE EDUCACIÓN"), ["metalife", "educacion"]
        )

    def test_puntuacion_ignorada(self):
        self.assertEqual(
            _normalizar_nombre("GASTOS MEDICOS MEDICALIFE FAM."),
            ["gastos", "medicos", "medicalife", "fam"],
        )

    def test_vacio(self):
        self.assertEqual(_normalizar_nombre(""), [])
        self.assertEqual(_normalizar_nombre(None), [])


class TestMapearProductoMetlife(TransactionCase):
    """Canonical MetLife rules ported from the Convertidor BCA."""

    def test_vida_prefijos_metalife(self):
        self.assertEqual(
            mapear_producto_metlife("METALIFE RETIRO", "vida"),
            "MetLife Metalife Retiro",
        )
        self.assertEqual(
            mapear_producto_metlife("METALIFE TU FUTURO", "vida"),
            "MetLife Metalife tu Futuro",
        )
        self.assertEqual(
            mapear_producto_metlife("METALIFE EDUCACION", "vida"),
            "Metlife Educalife",
        )
        self.assertEqual(
            mapear_producto_metlife("METALIFE MUJER", "vida"),
            "MetLife Metalife Mujer",
        )

    def test_vida_equivalentes_semanticos(self):
        self.assertEqual(
            mapear_producto_metlife("ORDINARIO DE VIDA", "vida"),
            "MetLife TotalLife",
        )
        self.assertEqual(
            mapear_producto_metlife("PLAN PERSONAL DE RETIRO", "vida"),
            "MetLife Metalife Retiro",
        )
        self.assertEqual(
            mapear_producto_metlife("CUENTA ESPECIAL AHORRO", "vida"),
            "MetLife Metalife Retiro",
        )
        self.assertEqual(
            mapear_producto_metlife("PERFECTLIFE", "vida"),
            "MetLife PerfectLife",
        )

    def test_vida_limpieza_ruido(self):
        self.assertEqual(
            mapear_producto_metlife("HORIZONTE PL 10", "vida"),
            "Metlife Horizonte",
        )
        self.assertEqual(
            mapear_producto_metlife("FLEXI LIFE INVERSION", "vida"),
            "Metlife FlexiLife",
        )
        self.assertEqual(
            mapear_producto_metlife("VIDA PAGOS LIMITADOS", "vida"),
            "MetLife Vida Pagos",
        )

    def test_vida_temporal_discrimina_gprp(self):
        self.assertEqual(
            mapear_producto_metlife("TEMPORAL EDUCALIFE", "vida"),
            "MetLife TempoLife GP/RP",
        )
        self.assertEqual(
            mapear_producto_metlife("TEMPORAL GRANDES SUMAS", "vida"),
            "MetLife TempoLife GP/RP",
        )
        self.assertEqual(
            mapear_producto_metlife("TEMPORAL", "vida"),
            "MetLife TempoLife",
        )
        self.assertEqual(
            mapear_producto_metlife("TEMPOLIFE", "vida"),
            "MetLife TempoLife",
        )

    def test_gmm_reglas(self):
        self.assertEqual(
            mapear_producto_metlife("GASTOS MEDICOS MEDICALIFE FAM.", "gmm"),
            "MetLife MedicaLife",
        )
        self.assertEqual(
            mapear_producto_metlife("PRIMORDIAL", "gmm"),
            "MetLife Primordial",
        )
        self.assertEqual(
            mapear_producto_metlife("GRUPO VIDA", "gmm"),
            "Grupo vida",
        )

    def test_sin_equivalente_devuelve_none(self):
        self.assertIsNone(mapear_producto_metlife("A.P. ESCOLAR", "vida"))
        self.assertIsNone(mapear_producto_metlife("GRUPO VIDA", "vida"))
        self.assertIsNone(mapear_producto_metlife("", "vida"))
        self.assertIsNone(mapear_producto_metlife(None, "vida"))
        self.assertIsNone(mapear_producto_metlife("XYZ DESCONOCIDO", "vida"))


class _ProductoFixtures(TransactionCase):
    """Real MetLife catalog (16 products) as seed for resolver tests."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.aseguradora = cls.env["res.partner"].create(
            {"name": "MetLife Test", "bca_tipo": "aseguradora"}
        )
        cls.Producto = cls.env["product.template"]

        def _crear(name, ramo):
            return cls.Producto.create(
                {
                    "name": name,
                    "bca_es_producto_seguro": True,
                    "bca_aseguradora_id": cls.aseguradora.id,
                    "bca_ramo": ramo,
                }
            )

        cls.grupo_vida = _crear("Grupo vida", "gmm")
        cls.educalife = _crear("Metlife Educalife", "vida")
        cls.flexilife = _crear("Metlife FlexiLife", "vida")
        cls.horizonte = _crear("Metlife Horizonte", "vida")
        cls.medicalife = _crear("MetLife MedicaLife", "gmm")
        cls.educacion = _crear("MetLife Educacion", "vida")
        cls.metalife_mujer = _crear("MetLife Metalife Mujer", "vida")
        cls.metalife_retiro = _crear("MetLife Metalife Retiro", "vida")
        cls.metalife_tu_futuro = _crear("MetLife Metalife tu Futuro", "vida")
        cls.perfectlife = _crear("MetLife PerfectLife", "vida")
        cls.primordial = _crear("MetLife Primordial", "gmm")
        cls.tempolife = _crear("MetLife TempoLife", "vida")
        cls.tempolife_gprp = _crear("MetLife TempoLife GP/RP", "vida")
        cls.totallife = _crear("MetLife TotalLife", "vida")
        cls.universales = _crear("MetLife Universales", "vida")
        cls.vida_pagos = _crear("MetLife Vida Pagos", "vida")


class TestResolverProductoReglas(_ProductoFixtures):
    """Real carátula crudos → products via canonical MetLife rules."""

    def test_educacion_va_a_educalife(self):
        """'METALIFE EDUCACION' (con y sin acento) → EducaLife, no Educación."""
        for crudo in ("METALIFE EDUCACION", "METALIFE EDUCACIÓN"):
            producto, warning = resolver_producto(
                self.env, crudo, "vida", self.aseguradora.id
            )
            self.assertEqual(producto, self.educalife)
            self.assertIsNone(warning)

    def test_mujer_va_a_metalife_mujer(self):
        producto, warning = resolver_producto(
            self.env, "METALIFE MUJER", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.metalife_mujer)
        self.assertIsNone(warning)

    def test_horizonte_pl10(self):
        producto, warning = resolver_producto(
            self.env, "HORIZONTE PL 10", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.horizonte)
        self.assertIsNone(warning)

    def test_flexi_life_inversion(self):
        producto, warning = resolver_producto(
            self.env, "FLEXI LIFE INVERSION", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.flexilife)
        self.assertIsNone(warning)

    def test_metalife_retiro(self):
        producto, warning = resolver_producto(
            self.env, "METALIFE RETIRO", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.metalife_retiro)
        self.assertIsNone(warning)

    def test_metalife_tu_futuro(self):
        producto, warning = resolver_producto(
            self.env, "METALIFE TU FUTURO", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.metalife_tu_futuro)
        self.assertIsNone(warning)

    def test_equivalente_semantico_ordinario_totalife(self):
        producto, warning = resolver_producto(
            self.env, "ORDINARIO DE VIDA", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.totallife)
        self.assertIsNone(warning)

    def test_totalife(self):
        producto, warning = resolver_producto(
            self.env, "TOTALIFE", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.totallife)
        self.assertIsNone(warning)

    def test_tempo_discrimina_gprp(self):
        producto, warning = resolver_producto(
            self.env, "TEMPORAL EDUCALIFE", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.tempolife_gprp)
        self.assertIsNone(warning)

    def test_temposimple(self):
        producto, warning = resolver_producto(
            self.env, "TEMPOLIFE", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.tempolife)
        self.assertIsNone(warning)

    def test_gmm_medicalife_familiar(self):
        producto, warning = resolver_producto(
            self.env, "GASTOS MEDICOS MEDICALIFE FAM.", "gmm", self.aseguradora.id
        )
        self.assertEqual(producto, self.medicalife)
        self.assertIsNone(warning)

    def test_gmm_primordial(self):
        producto, warning = resolver_producto(
            self.env, "PRIMORDIAL", "gmm", self.aseguradora.id
        )
        self.assertEqual(producto, self.primordial)
        self.assertIsNone(warning)

    def test_gmm_grupo_vida(self):
        producto, warning = resolver_producto(
            self.env, "GRUPO VIDA", "gmm", self.aseguradora.id
        )
        self.assertEqual(producto, self.grupo_vida)
        self.assertIsNone(warning)


class TestResolverProductoFallback(_ProductoFixtures):
    """Fuzzy matching, hard ramo, ambiguity, and failure paths."""

    def test_no_cruza_productos_entre_ramos(self):
        producto, warning = resolver_producto(
            self.env, "PRIMORDIAL", "vida", self.aseguradora.id
        )
        self.assertIsNone(producto)
        self.assertIsNotNone(warning)

    def test_case_insensitive_mix(self):
        producto, warning = resolver_producto(
            self.env, "UNIVERSALES", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.universales)
        self.assertIsNone(warning)

    def test_exacto_gana(self):
        producto, warning = resolver_producto(
            self.env, "Metlife FlexiLife", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.flexilife)
        self.assertIsNone(warning)

    def test_sin_match(self):
        producto, warning = resolver_producto(
            self.env, "XYZ PRODUCTO INEXISTENTE", "vida", self.aseguradora.id
        )
        self.assertIsNone(producto)
        self.assertIsNotNone(warning)

    def test_nombre_vacio(self):
        producto, warning = resolver_producto(
            self.env, "", "vida", self.aseguradora.id
        )
        self.assertIsNone(producto)
        self.assertIsNotNone(warning)

    def test_aseguradora_incorrecta(self):
        """Aseguradora distinta → sin match aunque la regla acierte."""
        otras = self.env["res.partner"].create({"name": "Otra Aseguradora"})
        producto, warning = resolver_producto(
            self.env, "PRIMORDIAL", "gmm", otras.id
        )
        self.assertIsNone(producto)
        self.assertIsNotNone(warning)

    def test_regla_sin_producto_en_catalogo(self):
        """Regla acierta pero el producto no existe en catálogo → aviso, no fuzzy."""
        self.metalife_tu_futuro.write({"bca_es_producto_seguro": False})
        producto, warning = resolver_producto(
            self.env, "METALIFE TU FUTURO", "vida", self.aseguradora.id
        )
        self.assertIsNone(producto)
        self.assertIsNotNone(warning)
        self.assertIn("según la regla", warning)


class TestResolverProductoAmbiguo(_ProductoFixtures):

    def test_ambiguo_advertido(self):
        """Ambigüedad fuzzy advertida cuando NO hay regla canónica."""
        extra = self.Producto.create(
            {
                "name": "MetLife Universales Plus",
                "bca_es_producto_seguro": True,
                "bca_aseguradora_id": self.aseguradora.id,
                "bca_ramo": "vida",
            }
        )
        self.addCleanup(extra.unlink)
        producto, warning = resolver_producto(
            self.env, "METALIFE UNIVERSALES", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.universales)
        self.assertIsNotNone(warning)
        self.assertIn("ambiguo", warning)


class TestCaratulasReales(_ProductoFixtures):
    """End-to-end: 10 carátulas reales → extractor → resolver_producto.

    Reads the raw text fixtures (1:1 con los PDFs reales), los pasa por el
    extractor de layout y después valida que `resolver_producto` acierte el
    producto del catálogo real esperado, sin advertencias.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.FIXTURES_DIR = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures"
        )
        cls.ext_vida = MetlifeVidaExtractor()
        cls.ext_gmm = MetlifeGmmExtractor()

    def _caratula(self, poliza: str) -> str:
        """Load fixture text by póliza (mismo matching que test_extractors)."""
        basename = poliza.lstrip("0")
        candidates = [
            f
            for f in os.listdir(self.FIXTURES_DIR)
            if f.startswith("000") and f.lstrip("0").startswith(basename)
        ]
        self.assertTrue(candidates, f"Fixture no encontrado para {poliza}")
        path = os.path.join(self.FIXTURES_DIR, sorted(candidates)[0])
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()

    def _resolve(self, poliza: str, ramo: str, esperado):
        texto = self._caratula(poliza)
        data = (
            self.ext_gmm.extract(texto)
            if ramo == "gmm"
            else self.ext_vida.extract(texto)
        )
        self.assertTrue(
            data.get("producto_pdf"),
            f"{poliza}: producto_pdf no extraído, layout {ramo}",
        )
        producto, warning = resolver_producto(
            self.env, data["producto_pdf"], ramo, self.aseguradora.id
        )
        self.assertEqual(
            producto, esperado,
            f"{poliza}: '{data['producto_pdf']}' → {producto and producto.display_name}, "
            f"esperado {esperado.display_name}",
        )
        self.assertIsNone(warning, f"{poliza}: warning inesperado: {warning}")
        return data["producto_pdf"]

    def test_caratulas_gmm(self):
        gmm = {
            "0001420597": ("GASTOS MEDICOS MEDICALIFE FAM.", self.medicalife),
            "0000018128": ("PRIMORDIAL", self.primordial),
        }
        for poliza, (crudo, producto) in gmm.items():
            self.assertEqual(
                self._resolve(poliza, "gmm", producto), crudo, poliza
            )

    def test_caratulas_vida(self):
        vida = {
            "8497462": ("TEMPOLIFE", self.tempolife),
            "8495803": ("FLEXI LIFE INVERSION", self.flexilife),
            "8493880": ("METALIFE MUJER", self.metalife_mujer),
            "8497494": ("TOTALIFE", self.totallife),
            "8494374": ("HORIZONTE PL 10", self.horizonte),
            "8496336": ("METALIFE EDUCACIÓN", self.educalife),
            "8497472": ("METALIFE RETIRO", self.metalife_retiro),
            "8495582": ("METALIFE TU FUTURO", self.metalife_tu_futuro),
        }
        for poliza, (crudo, producto) in vida.items():
            self.assertEqual(
                self._resolve(poliza, "vida", producto), crudo, poliza
            )
