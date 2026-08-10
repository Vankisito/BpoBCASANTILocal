from __future__ import annotations

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestPromotoriaGovernance(TransactionCase):
    """Stored Promotoría dimensions and controlled network changes."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        Partner = cls.env['res.partner']
        cls.holding = Partner.create({
            'name': 'Holding Governance',
            'bca_tipo': 'holding',
        })
        cls.promotoria_a = Partner.create({
            'name': 'Promotoría Governance A',
            'bca_tipo': 'promotoria',
            'parent_id': cls.holding.id,
        })
        cls.promotoria_b = Partner.create({
            'name': 'Promotoría Governance B',
            'bca_tipo': 'promotoria',
            'parent_id': cls.holding.id,
        })
        cls.agente = Partner.create({
            'name': 'Agente Governance',
            'bca_tipo': 'agente',
            'parent_id': cls.promotoria_a.id,
        })

    def test_dimensions_are_stored_and_indexed(self) -> None:
        Poliza = self.env['bca.poliza']
        Partner = self.env['res.partner']
        self.assertTrue(Poliza._fields['promotoria_id'].store)
        self.assertTrue(Poliza._fields['promotoria_id'].index)
        self.assertTrue(Partner._fields['bca_promotoria_id'].store)
        self.assertTrue(Partner._fields['bca_promotoria_id'].index)
        self.assertEqual(self.agente.bca_promotoria_id, self.promotoria_a)

    def test_group_by_promotoria_is_sql_capable(self) -> None:
        Poliza = self.env['bca.poliza']
        groups = Poliza._read_group(
            [('agente_id', '=', self.agente.id)],
            ['promotoria_id'],
            ['__count'],
        )
        self.assertEqual(len(groups), 0)

    def test_invalid_network_entities_are_rejected(self) -> None:
        Partner = self.env['res.partner']
        with self.assertRaises(ValidationError):
            Partner.create({'name': 'Agente sin Promotoría', 'bca_tipo': 'agente'})
        with self.assertRaises(ValidationError):
            Partner.create({
                'name': 'Promotoría sin Holding',
                'bca_tipo': 'promotoria',
            })

    def test_direct_affiliation_change_is_blocked(self) -> None:
        with self.assertRaises(UserError):
            self.agente.write({'parent_id': self.promotoria_b.id})

    def test_wizard_changes_affiliation_and_creates_audit(self) -> None:
        director = self.env.ref('base.user_admin')
        director.group_ids = [
            (4, self.env.ref('BCA_Seguros.group_bca_director').id),
        ]
        wizard = self.env['bca.wizard.cambio.promotoria'].with_user(director).create({
            'agente_id': self.agente.id,
            'promotoria_nueva_id': self.promotoria_b.id,
            'motivo': 'Transferencia de prueba',
        })
        wizard.action_confirmar()
        self.assertEqual(self.agente.parent_id, self.promotoria_b)
        cambio = self.env['bca.agente.cambio.promotoria'].search([
            ('agente_id', '=', self.agente.id),
        ], order='id desc', limit=1)
        self.assertEqual(cambio.promotoria_anterior_id, self.promotoria_a)
        self.assertEqual(cambio.promotoria_nueva_id, self.promotoria_b)

    def test_audit_model_cannot_be_written_directly(self) -> None:
        with self.assertRaises(AccessError):
            self.env['bca.agente.cambio.promotoria'].create({
                'agente_id': self.agente.id,
                'promotoria_nueva_id': self.promotoria_b.id,
                'motivo': 'Escritura no autorizada',
            })