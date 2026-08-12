from __future__ import annotations

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestIndependenciaFiscal(TransactionCase):
    """Independencia fiscal de la red BCA (v19.0.1.9.0).

    Promotorías y agentes (persona física o moral) conservan su propio RFC (`vat`)
    y domicilio; NO los heredan del ancestro por la jerarquía. Los contactos-persona
    normales (sin bca_tipo) SÍ mantienen la herencia nativa.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        # Holding con RFC propio (persona moral, raíz de la red).
        cls.holding = cls.Partner.create({
            'name': 'Holding BCA Test',
            'bca_tipo': 'holding',
            'is_company': True,
            'vat': 'HOL010101AAA',
            'street': 'Calle Holding 1',
        })

    # ------------------------------------------------------------------ RFC
    def test_promotoria_moral_conserva_rfc(self):
        promo = self.Partner.create({
            'name': 'Promotoría Moral',
            'bca_tipo': 'promotoria',
            'parent_id': self.holding.id,
            'is_company': True,
            'vat': 'PMO020202BBB',
        })
        self.assertEqual(promo.vat, 'PMO020202BBB')

    def test_promotoria_fisica_no_hereda_rfc(self):
        """Caso crítico: persona física (is_company=False) NO debe heredar el RFC
        del holding pese a que su commercial_partner_id nativo sería el holding."""
        promo = self.Partner.create({
            'name': 'Promotoría Física',
            'bca_tipo': 'promotoria',
            'parent_id': self.holding.id,
            'is_company': False,
            'vat': 'PMF030303CCC',
        })
        self.assertEqual(promo.vat, 'PMF030303CCC')
        self.assertNotEqual(promo.vat, self.holding.vat)

    def test_agente_fisico_conserva_rfc_bajo_promotoria(self):
        promo = self.Partner.create({
            'name': 'Promotoría Moral 2',
            'bca_tipo': 'promotoria',
            'parent_id': self.holding.id,
            'is_company': True,
            'vat': 'PMO020202BBB',
        })
        agente = self.Partner.create({
            'name': 'Agente Físico',
            'bca_tipo': 'agente',
            'parent_id': promo.id,
            'is_company': False,
            'vat': 'AGT040404DDD',
        })
        self.assertEqual(agente.vat, 'AGT040404DDD')
        self.assertNotEqual(agente.vat, promo.vat)

    def test_editar_rfc_holding_no_contamina_descendientes(self):
        """DOWNSTREAM: cambiar el RFC del holding (con hijos ya creados) no debe
        sobrescribir el de promotorías/agentes (física o moral)."""
        promo_fisica = self.Partner.create({
            'name': 'Promotoría Física DS',
            'bca_tipo': 'promotoria',
            'parent_id': self.holding.id,
            'is_company': False,
            'vat': 'PMF030303CCC',
        })
        agente = self.Partner.create({
            'name': 'Agente DS',
            'bca_tipo': 'agente',
            'parent_id': promo_fisica.id,
            'is_company': False,
            'vat': 'AGT040404DDD',
        })
        self.holding.write({'vat': 'HOL999999ZZZ'})
        promo_fisica.invalidate_recordset()
        agente.invalidate_recordset()
        self.assertEqual(promo_fisica.vat, 'PMF030303CCC')
        self.assertEqual(agente.vat, 'AGT040404DDD')

    # ------------------------------------------------------------- Domicilio
    def test_domicilio_no_se_hereda(self):
        """El domicilio del holding no debe copiarse a promotorías/agentes
        (ni siquiera a una promotoría moral con type='contact')."""
        promo = self.Partner.create({
            'name': 'Promotoría Domicilio',
            'bca_tipo': 'promotoria',
            'parent_id': self.holding.id,
            'is_company': True,
            'vat': 'PMO020202BBB',
            'street': 'Avenida Promotoría 500',
        })
        self.assertEqual(promo.street, 'Avenida Promotoría 500')
        # Cambiar el domicilio del holding no debe empujarse hacia abajo.
        self.holding.write({'street': 'Nueva Calle Holding 2'})
        promo.invalidate_recordset()
        self.assertEqual(promo.street, 'Avenida Promotoría 500')

    # -------------------------------------------------- Regresión inversa
    def test_contacto_normal_si_hereda_del_holding(self):
        """Un contacto-persona normal (sin bca_tipo) colgado del holding SÍ debe
        heredar el RFC y domicilio de la empresa (comportamiento nativo intacto).
        Es el caso 'empleados de Grupo BCA'."""
        empleado = self.Partner.create({
            'name': 'Empleado Normal',
            'parent_id': self.holding.id,
            'is_company': False,
            'type': 'contact',
        })
        self.assertEqual(empleado.vat, self.holding.vat)
        self.assertEqual(empleado.street, self.holding.street)
