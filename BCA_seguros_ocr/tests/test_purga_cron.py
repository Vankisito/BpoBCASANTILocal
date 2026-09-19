"""Prueba del cron de purga de documentos OCR (retención a 30 días).

Valida `_cron_purga_documentos_antiguos`: purga registros con
`create_date < hoy - 30 días` salvo los que están ``procesando``, y
conserva los recientes.

Run via Odoo test runner:

    odoo --test-enable --test-tags '/BCA_seguros_ocr'
"""

from __future__ import annotations

import base64
from datetime import timedelta

from odoo.fields import Datetime
from odoo.tests.common import TransactionCase, tagged


@tagged("BCA_seguros_ocr")
class TestPurgaDocumentosOcr(TransactionCase):
    """Retención y limpieza de carátulas (privacidad)."""

    DIA_31 = timedelta(days=31)
    DIA_10 = timedelta(days=10)

    def _crear_documento(self, estado: str = "extraido"):
        return self.env["bca.ocr.documento"].create(
            {
                "archivo_pdf": base64.b64encode(b"%PDF-1.4 test caratula"),
                "archivo_nombre": "caratula_test.pdf",
                "estado": estado,
            }
        )

    def _backdatear(self, doc, dias) -> None:
        self.env.cr.execute(
            "UPDATE bca_ocr_documento SET create_date = %s WHERE id = %s",
            (Datetime.now() - dias, doc.id),
        )
        doc.invalidate_recordset(["create_date"])

    def _correr_cron(self) -> None:
        self.env["bca.ocr.documento"]._cron_purga_documentos_antiguos()

    def test_purga_documento_antiguo_extraido(self) -> None:
        doc = self._crear_documento("extraido")
        self._backdatear(doc, self.DIA_31)
        self._correr_cron()
        self.assertFalse(doc.exists())

    def test_purga_documento_antiguo_abandonado(self) -> None:
        doc = self._crear_documento("nuevo")
        self._backdatear(doc, self.DIA_31)
        self._correr_cron()
        self.assertFalse(doc.exists())

    def test_respeta_documento_reciente(self) -> None:
        doc = self._crear_documento("extraido")
        self._backdatear(doc, self.DIA_10)
        self._correr_cron()
        self.assertTrue(doc.exists())

    def test_respeta_documento_procesando(self) -> None:
        doc = self._crear_documento("procesando")
        self._backdatear(doc, self.DIA_31)
        self._correr_cron()
        self.assertTrue(doc.exists(), "un documento en extracción no debe purgarse")

    def test_elimina_attachment_del_pdf(self) -> None:
        doc = self._crear_documento("extraido")
        # sudo: las record rules de ir.attachment ocultan el PDF de la búsqueda
        # no-superusuario (el modelo OCR no es mail.thread).
        # skip_res_field_check: Odoo 19 excluye por defecto los attachments de
        # campos binary (res_field != False) de la búsqueda.
        attach = (
            self.env["ir.attachment"]
            .sudo()
            .with_context(skip_res_field_check=True)
            .search(
                [
                    ("res_model", "=", "bca.ocr.documento"),
                    ("res_id", "=", doc.id),
                ]
            )
        )
        self.assertTrue(attach, "el PDF debe persistirse como attachment")
        self._backdatear(doc, self.DIA_31)
        self._correr_cron()
        self.assertFalse(
            attach.exists(), "al purgar el documento, el PDF va en cascada"
        )
