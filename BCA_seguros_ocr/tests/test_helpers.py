"""Unit tests for OCR → Odoo resolver helpers.

Validates `resolver_producto` fuzzy matching: case/accent-insensitive
word matching, soft ramo fallback, and ambiguity warnings.

Run via Odoo test runner:

    odoo --test-enable --test-tags '/BCA_seguros_ocr'
"""

from __future__ import annotations

from odoo.tests.common import TransactionCase

from ..helpers import _normalizar_nombre, resolver_producto


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


class _ProductoFixtures(TransactionCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.aseguradora = cls.env["res.partner"].create(
            {"name": "MetLife Test", "bca_tipo": "aseguradora"}
        )
        Producto = cls.env["product.template"]

        cls.primordial = Producto.create(
            {
                "name": "Metlife Primordial",
                "bca_es_producto_seguro": True,
                "bca_aseguradora_id": cls.aseguradora.id,
                "bca_ramo": "vida",
            }
        )
        cls.medical = Producto.create(
            {
                "name": "Metlife Gastos Médicos Medicalife Familiar",
                "bca_es_producto_seguro": True,
                "bca_aseguradora_id": cls.aseguradora.id,
                "bca_ramo": "gmm",
            }
        )
        cls.educacion = Producto.create(
            {
                "name": "Metlife Educación",
                "bca_es_producto_seguro": True,
                "bca_aseguradora_id": cls.aseguradora.id,
                "bca_ramo": "vida",
            }
        )
        cls.mujer = Producto.create(
            {
                "name": "Metlife Mujer",
                "bca_es_producto_seguro": True,
                "bca_aseguradora_id": cls.aseguradora.id,
                "bca_ramo": "vida",
            }
        )


class TestResolverProducto(_ProductoFixtures):

    def test_case_insensitive_mix(self):
        """Carátula 'PRIMORDIAL' matchea producto 'Metlife Primordial'."""
        producto, warning = resolver_producto(
            self.env, "PRIMORDIAL", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.primordial)
        self.assertIsNone(warning)

    def test_ramo_soft_fallback(self):
        """Ramo carátula gmm ≠ ramo producto vida → fallback sin ramo."""
        producto, warning = resolver_producto(
            self.env, "PRIMORDIAL", "gmm", self.aseguradora.id
        )
        self.assertEqual(producto, self.primordial)
        self.assertIsNotNone(warning)
        self.assertIn("sin filtrar", warning)

    def test_acentos_normalizados(self):
        """'METALIFE EDUCACION' sin acento matchea 'Metlife Educación'."""
        producto, warning = resolver_producto(
            self.env, "METALIFE EDUCACION", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.educacion)
        self.assertIsNone(warning)

    def test_typo_ocr_tolerado(self):
        """'METALIFE MUJER' (carátula) matchea 'Metlife Mujer' (catálogo)."""
        producto, warning = resolver_producto(
            self.env, "METALIFE MUJER", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.mujer)
        self.assertIsNone(warning)

    def test_exacto_gana(self):
        producto, warning = resolver_producto(
            self.env, "Metlife Primordial", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.primordial)
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
        """Aseguradora distinta → sin match aunque nombre exista."""
        otras = self.env["res.partner"].create({"name": "Otra Aseguradora"})
        producto, warning = resolver_producto(
            self.env, "PRIMORDIAL", "vida", otras.id
        )
        self.assertIsNone(producto)
        self.assertIsNotNone(warning)


class TestResolverProductoAmbiguo(_ProductoFixtures):

    def test_ambiguo_advertido(self):
        extra = self.env["product.template"].create(
            {
                "name": "Metlife Primordial Plus",
                "bca_es_producto_seguro": True,
                "bca_aseguradora_id": self.aseguradora.id,
                "bca_ramo": "vida",
            }
        )
        self.addCleanup(extra.unlink)
        producto, warning = resolver_producto(
            self.env, "PRIMORDIAL", "vida", self.aseguradora.id
        )
        self.assertEqual(producto, self.primordial)
        self.assertIsNotNone(warning)
        self.assertIn("ambiguo", warning)