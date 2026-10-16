from __future__ import annotations

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDisplayNameRed(TransactionCase):
    """Representación de la red BCA (v19.0.1.11.0).

    Agente y Promotoría muestran SOLO su nombre en `display_name` (sin la
    empresa madre). Un contacto normal colgado de una empresa conserva el
    formato nativo "Empresa, Contacto". La relación parent_id (base de
    comisiones y reportes) permanece intacta.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.holding = cls.Partner.create({
            'name': 'Grupo BCA',
            'bca_tipo': 'holding',
            'is_company': True,
        })

    def test_agente_y_promotoria_muestran_solo_su_nombre(self):
        promotoria = self.Partner.create({
            'name': 'Agencia BCA Monterrey',
            'bca_tipo': 'promotoria',
            'parent_id': self.holding.id,
            'is_company': True,
        })
        agente = self.Partner.create({
            'name': 'Juan Pérez Hernández',
            'bca_tipo': 'agente',
            'parent_id': promotoria.id,
            'is_company': False,
        })
        self.assertEqual(promotoria.display_name, 'Agencia BCA Monterrey')
        self.assertEqual(agente.display_name, 'Juan Pérez Hernández')
        # La relación de red se conserva (alimenta comisiones y reportes).
        self.assertEqual(agente.parent_id, promotoria)
        self.assertEqual(promotoria.parent_id, self.holding)

    def test_promotoria_persona_fisica_muestra_solo_su_nombre(self):
        promotoria = self.Partner.create({
            'name': 'Agencia Norte',
            'bca_tipo': 'promotoria',
            'parent_id': self.holding.id,
            'is_company': False,
        })
        self.assertEqual(promotoria.display_name, 'Agencia Norte')

    def test_contacto_normal_conserva_formato_nativo(self):
        empleado = self.Partner.create({
            'name': 'Empleado Normal',
            'parent_id': self.holding.id,
            'is_company': False,
            'type': 'contact',
        })
        self.assertEqual(empleado.display_name, 'Grupo BCA, Empleado Normal')
