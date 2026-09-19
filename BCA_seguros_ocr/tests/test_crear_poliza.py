"""Flujo OCR → creación de póliza: duplicados protegidos (R-POL-01).

Valida que ``_crear_poliza_from_staging`` anticipe con mensaje amigable la
creación de una póliza cuyo número ya existe para la misma aseguradora, en
vez de dejar caer un ConstraintError crudo de postgres.

Run via Odoo test runner:

    odoo --test-enable --test-tags '/BCA_seguros_ocr'
"""

from __future__ import annotations

import base64

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("BCA_seguros_ocr")
class TestCrearPolizaDuplicada(TransactionCase):
    """Duplicados de número de póliza se rechazan antes de crear."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        Partner = cls.env["res.partner"]
        cls.aseguradora = cls.env.ref("BCA_Seguros.partner_metlife")
        cls.agente = Partner.create({"name": "Agente OCR Dup Test"})
        cls.contratante = Partner.create({"name": "Cliente OCR Dup Test"})
        cls.producto = cls.env["product.template"].create(
            {
                "name": "Vida OCR Dup Test",
                "bca_es_producto_seguro": True,
                "bca_aseguradora_id": cls.aseguradora.id,
                "bca_ramo": "vida",
            }
        )

    def _crear_poliza(self, name: str):
        return self.env["bca.poliza"].create(
            {
                "name": name,
                "aseguradora_id": self.aseguradora.id,
                "producto_id": self.producto.id,
                "agente_id": self.agente.id,
                "contratante_id": self.contratante.id,
                "periodicidad": "anual",
                "fecha_inicio": "2026-01-01",
                "fecha_fin": "2027-01-01",
                "prima_anual": 1.0,
            }
        )

    def _crear_documento(self, poliza_numero: str):
        return self.env["bca.ocr.documento"].create(
            {
                "archivo_pdf": base64.b64encode(b"%PDF-1.4 test caratula"),
                "archivo_nombre": "caratula_test.pdf",
                "poliza_numero": poliza_numero,
            }
        )

    def test_crear_poliza_duplicada_lanza_usererror(self) -> None:
        self._crear_poliza("POL-OCR-DUP")
        doc = self._crear_documento("POL-OCR-DUP")
        with self.assertRaisesRegex(UserError, "Ya existe la póliza"):
            doc._crear_poliza_from_staging()

    def test_crear_poliza_sin_duplicado_no_dice_existe(self) -> None:
        doc = self._crear_documento("POL-OCR-NUEVA")
        try:
            doc._crear_poliza_from_staging()
        except UserError as exc:
            self.assertNotIn(
                "Ya existe la póliza",
                str(exc),
                "Sin duplicado el flujo debe continuar y fallar por otra causa",
            )
        else:
            self.fail("Esperaba UserError por datos incompletos del documento")
