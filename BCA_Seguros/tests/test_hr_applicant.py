from __future__ import annotations

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestHrApplicant(TransactionCase):
    """Etapa 3 — hr.applicant: creación automática de res.partner BCA."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.holding = cls.env.ref('BCA_Seguros.partner_bca_holding')
        cls.job_captacion = cls.env.ref('BCA_Seguros.job_captacion_promotoria')
        cls.job_reclutamiento = cls.env.ref('BCA_Seguros.job_reclutamiento_agente')

        cls.promotoria = cls.env['res.partner'].create({
            'name': 'Promotoría Origen',
            'bca_tipo': 'promotoria',
            'parent_id': cls.holding.id,
        })

        Stage = cls.env['hr.recruitment.stage']
        cls.stage_open = Stage.create({'name': 'Test - En Proceso', 'sequence': 1})
        cls.stage_hired = Stage.create({
            'name': 'Test - Contratado',
            'sequence': 10,
            'hired_stage': True,
        })

        cls.job_estandar = cls.env['hr.job'].create({'name': 'Puesto estándar RH'})

    def _crear_applicant(self, job, **overrides) -> object:
        vals = {
            'partner_name': 'Candidato Test',
            'job_id': job.id,
            'stage_id': self.stage_open.id,
            'email_from': 'candidato@example.com',
        }
        vals.update(overrides)
        return self.env['hr.applicant'].create(vals)

    def test_contratado_reclutamiento_crea_agente(self) -> None:
        """Applicant de Reclutamiento de Agente → crea res.partner agente."""
        applicant = self._crear_applicant(
            self.job_reclutamiento,
            partner_name='Juan Agente',
            bca_promotoria_destino_id=self.promotoria.id,
        )
        applicant.stage_id = self.stage_hired
        self.assertTrue(applicant.partner_id, 'Debe crearse partner_id.')
        self.assertEqual(applicant.partner_id.bca_tipo, 'agente')
        self.assertEqual(applicant.partner_id.parent_id, self.promotoria)
        self.assertEqual(applicant.partner_id.name, 'Juan Agente')

    def test_contratado_captacion_crea_promotoria(self) -> None:
        """Applicant de Captación de Promotoría → crea res.partner promotoría."""
        applicant = self._crear_applicant(
            self.job_captacion,
            partner_name='Nueva Promotoría SA',
        )
        applicant.stage_id = self.stage_hired
        self.assertTrue(applicant.partner_id)
        self.assertEqual(applicant.partner_id.bca_tipo, 'promotoria')
        self.assertEqual(applicant.partner_id.parent_id, self.holding)
        self.assertEqual(applicant.partner_id.name, 'Nueva Promotoría SA')

    def test_reclutamiento_sin_promotoria_destino_error(self) -> None:
        """Reclutamiento de Agente sin promotoría destino → UserError."""
        applicant = self._crear_applicant(self.job_reclutamiento)
        with self.assertRaises(UserError):
            applicant.stage_id = self.stage_hired

    def test_idempotencia_doble_hired(self) -> None:
        """Pasar dos veces por hired no duplica partner."""
        applicant = self._crear_applicant(
            self.job_captacion,
            partner_name='Promotoría Idempotente',
        )
        applicant.stage_id = self.stage_hired
        primer_partner = applicant.partner_id
        self.assertTrue(primer_partner)

        applicant.stage_id = self.stage_open
        applicant.stage_id = self.stage_hired
        self.assertEqual(applicant.partner_id, primer_partner,
                         'partner_id no debe cambiar en segunda transición.')

    def test_job_ajeno_no_crea_partner(self) -> None:
        """Applicant en job estándar (no BCA) → no se crea partner BCA."""
        applicant = self._crear_applicant(self.job_estandar)
        applicant.stage_id = self.stage_hired
        partner = applicant.partner_id
        if partner:
            self.assertNotIn(partner.bca_tipo, ('agente', 'promotoria'),
                             'Job ajeno no debe producir partner con bca_tipo BCA.')
