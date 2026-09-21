from __future__ import annotations

import base64

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestOcrSecurity(TransactionCase):
    """OCR documents contain personal data and must not be agent-visible."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        group_internal = cls.env.ref("base.group_user")
        cls.group_agent = cls.env.ref("BCA_Seguros.group_bca_agente")
        cls.group_operator = cls.env.ref("BCA_Seguros.group_bca_operador")
        User = cls.env["res.users"].with_context(no_reset_password=True)
        cls.agent = User.create(
            {
                "name": "OCR security agent",
                "login": "ocr_security_agent",
                "group_ids": [(6, 0, [group_internal.id, cls.group_agent.id])],
            }
        )
        cls.operator = User.create(
            {
                "name": "OCR security operator",
                "login": "ocr_security_operator",
                "group_ids": [(6, 0, [group_internal.id, cls.group_operator.id])],
            }
        )
        cls.document = cls.env["bca.ocr.documento"].create(
            {
                "archivo_pdf": base64.b64encode(b"not-a-real-pdf"),
                "archivo_nombre": "datos-personales.pdf",
            }
        )

    def test_agent_cannot_read_ocr_document(self) -> None:
        with self.assertRaises(AccessError):
            self.env["bca.ocr.documento"].with_user(self.agent).read(
                ["archivo_pdf"]
            )

    def test_operator_can_read_ocr_document(self) -> None:
        values = self.env["bca.ocr.documento"].with_user(self.operator).read(
            ["archivo_nombre"]
        )
        self.assertEqual(values[0]["archivo_nombre"], "datos-personales.pdf")
