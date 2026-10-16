from __future__ import annotations

from datetime import date

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
        # Cartera mínima para ejercitar la búsqueda por contratante/asegurado y
        # el chatter desde el rol Promotor.
        cls.aseguradora = cls.env.ref('BCA_Seguros.partner_metlife')
        cls.producto = cls.env['product.template'].create({
            'name': 'Vida Promotor Security',
            'bca_es_producto_seguro': True,
            'bca_aseguradora_id': cls.aseguradora.id,
            'bca_ramo': 'vida',
        })
        cls.contratante_a = Partner.create({'name': 'Contratante Promo A'})
        cls.contratante_b = Partner.create({'name': 'Contratante Promo B'})
        cls.asegurado_a = Partner.create({'name': 'Asegurado Promo A'})
        cls.asegurado_b = Partner.create({'name': 'Asegurado Promo B'})
        poliza_base = {
            'aseguradora_id': cls.aseguradora.id,
            'producto_id': cls.producto.id,
            'fecha_inicio': date(2026, 1, 1),
            'fecha_fin': date(2027, 1, 1),
            'periodicidad': 'anual',
        }
        Poliza = cls.env['bca.poliza']
        cls.poliza_a = Poliza.create(dict(
            poliza_base, name='PSEC-A',
            agente_id=cls.agente_a.id,
            contratante_id=cls.contratante_a.id,
            asegurado_id=cls.asegurado_a.id,
        ))
        cls.poliza_b = Poliza.create(dict(
            poliza_base, name='PSEC-B',
            agente_id=cls.agente_b.id,
            contratante_id=cls.contratante_b.id,
            asegurado_id=cls.asegurado_b.id,
        ))

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

    def test_promotor_name_search_contratante(self) -> None:
        """BUG-024: el Promotor encuentra contratantes de SUS pólizas por
        name_search (alimenta el autocompletado del buscador de pólizas)."""
        Partner = self.env['res.partner'].with_user(self.promotor)
        encontrados = [pid for pid, _name in Partner.name_search(self.contratante_a.name)]
        self.assertIn(self.contratante_a.id, encontrados)
        self.assertNotIn(self.contratante_b.id, encontrados)

    def test_promotor_name_search_asegurado(self) -> None:
        """BUG-024: idem para el rol Asegurado."""
        Partner = self.env['res.partner'].with_user(self.promotor)
        encontrados = [pid for pid, _name in Partner.name_search(self.asegurado_a.name)]
        self.assertIn(self.asegurado_a.id, encontrados)
        self.assertNotIn(self.asegurado_b.id, encontrados)

    def test_promotor_puede_comentar_en_poliza(self) -> None:
        """BUG-025: el Promotor puede escribir notas/enviar mensajes en el
        chatter de una póliza de su promotoría pese a su ACL de solo lectura."""
        mensaje = self.poliza_a.with_user(self.promotor).message_post(
            body='Nota del promotor')
        self.assertTrue(mensaje)
        self.assertEqual(mensaje.author_id, self.promotor.partner_id)

    def test_promotor_no_puede_escribir_campos_poliza(self) -> None:
        """El fix del chatter NO otorga escritura de negocio al Promotor."""
        with self.assertRaises(AccessError):
            self.poliza_a.with_user(self.promotor).write({'plan': 'X'})
