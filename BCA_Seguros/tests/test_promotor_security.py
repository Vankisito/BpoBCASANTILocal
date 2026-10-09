from __future__ import annotations

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestPromotorSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        Partner = cls.env['res.partner']
        cls.holding = Partner.create({
            'name': 'Holding Promotor Security',
            'bca_tipo': 'holding',
        })
        cls.promotoria_a = Partner.create({
            'name': 'Promotoría Security A',
            'bca_tipo': 'promotoria',
            'parent_id': cls.holding.id,
        })
        cls.promotoria_b = Partner.create({
            'name': 'Promotoría Security B',
            'bca_tipo': 'promotoria',
            'parent_id': cls.holding.id,
        })
        cls.agente_a = Partner.create({
            'name': 'Agente Security A',
            'bca_tipo': 'agente',
            'parent_id': cls.promotoria_a.id,
        })
        cls.agente_b = Partner.create({
            'name': 'Agente Security B',
            'bca_tipo': 'agente',
            'parent_id': cls.promotoria_b.id,
        })
        cls.unrelated_contact = Partner.create({
            'name': 'Contacto No Relacionado Security',
        })
        cls.promotor = cls.env['res.users'].with_context(
            no_reset_password=True,
        ).create({
            'name': 'Promotor Security',
            'login': 'bca_test_promotor_security',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('BCA_Seguros.group_bca_promotor').id,
            ])],
        })
        cls.promotor.partner_id.write({'parent_id': cls.promotoria_a.id})
        cls.internal_user = cls.env['res.users'].with_context(
            no_reset_password=True,
        ).create({
            'name': 'Usuario Interno Security',
            'login': 'bca_test_internal_security',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_promotor_sees_only_affiliated_agents(self) -> None:
        visible = self.env['res.partner'].with_user(self.promotor).search([])
        self.assertIn(self.agente_a, visible)
        self.assertNotIn(self.agente_b, visible)
        self.assertIn(self.promotoria_a, visible)
        self.assertNotIn(self.promotoria_b, visible)
        self.assertNotIn(self.unrelated_contact, visible)

    def test_promotoria_user_ids_are_source_of_assignment(self) -> None:
        self.assertIn(self.promotor, self.promotoria_a.bca_promotor_user_ids)
        self.assertNotIn(self.promotor, self.promotoria_b.user_ids)

    def test_promotor_reads_contacts_required_by_native_flows(self) -> None:
        """Mail/Recruitment contacts are readable without opening all partners."""
        Partner = self.env['res.partner'].with_user(self.promotor)
        visible = Partner.search([])

        self.assertIn(self.internal_user.partner_id, visible)
        self.assertIn(self.promotor.company_id.partner_id, visible)

    def test_promotor_cannot_write_contacts(self) -> None:
        with self.assertRaises(AccessError):
            self.internal_user.partner_id.with_user(self.promotor).write({
                'comment': 'No debe modificarse por Promotor.',
            })

    def test_promotor_cannot_read_public_employee_directory(self) -> None:
        visible = self.env['hr.employee.public'].with_user(self.promotor).search([])
        self.assertFalse(visible)
