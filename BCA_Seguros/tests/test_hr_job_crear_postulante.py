from __future__ import annotations

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('BCA_Seguros')
class TestCrearPostulanteDesdePuesto(TransactionCase):
    """SI-2 — La Reclutadora BCA crea postulante desde el puesto de trabajo.

    Regresión de dos capas:
    1. El kanban nativo ocultaba el menú "Nuevo → Application" a la Reclutadora
       (solo Encargado) y action_hr_job_interviewer traía create=False.
    2. La regla SI-1 ('user_id == uid', perm_create) negaba el CREATE: el campo
       nativo user_id es compute store de job.user_id y el candidato nacía sin
       responsable o con uno ajeno. El fix (D-27) da default=env.user: todo
       candidato nace con su creadora como responsable.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.job_reclutamiento = cls.env.ref('BCA_Seguros.job_reclutamiento_agente')
        cls.stage_recibido = cls.env.ref('BCA_Seguros.stage_recibido')
        cls.grupo_reclutadora = cls.env.ref('BCA_Seguros.group_bca_reclutadora')

    def _reclutadora(self, login: str):
        return self.env['res.users'].create({
            'name': 'Reclutadora SI-2',
            'login': login,
            'group_ids': [
                (6, 0, [self.env.ref('base.group_user').id, self.grupo_reclutadora.id]),
            ],
        })

    def _vals_candidato(self, nombre: str, **overrides) -> dict:
        vals = {
            'job_id': self.job_reclutamiento.id,
            'partner_name': nombre,
            'stage_id': self.stage_recibido.id,
        }
        vals.update(overrides)
        return vals

    def test_reclutadora_crea_postulante_desde_puesto(self) -> None:
        """La Reclutadora crea un postulante del puesto sin Access Denied y nace
        con ella como responsable (regla SI-1 satisfecha al nacer)."""
        reclutadora = self._reclutadora('recl_si2_crea@test.com')
        applicant = self.env['hr.applicant'].with_user(reclutadora).create(
            self._vals_candidato('Postulante SI-2 Crea'),
        )
        self.assertTrue(applicant, 'Debe crearse el postulante.')
        self.assertEqual(applicant.job_id, self.job_reclutamiento)
        self.assertEqual(applicant.user_id, reclutadora,
                         'El responsable debe ser la creadora (D-27).')

    def test_reclutadora_ve_solo_su_postulante_del_puesto(self) -> None:
        """La Reclutadora ve SU postulante del puesto y no el de otra."""
        otra = self._reclutadora('recl_si2_otra@test.com')
        ajeno = self.env['hr.applicant'].create(
            self._vals_candidato('Postulante de Otra', user_id=otra.id),
        )
        reclutadora = self._reclutadora('recl_si2_blanca@test.com')
        propio = self.env['hr.applicant'].with_user(reclutadora).create(
            self._vals_candidato('Postulante SI-2 Blanco'),
        )
        visibles = self.env['hr.applicant'].with_user(reclutadora).search(
            [('job_id', '=', self.job_reclutamiento.id)],
        )
        self.assertIn(propio, visibles)
        self.assertNotIn(ajeno, visibles,
                         'La reclutadora NO debe ver el postulante de otra.')

    def test_accion_nativa_precarga_job(self) -> None:
        """La acción nativa action_hr_job_new_application precarga default_job_id
        desde el `active_id` (puesto activo del formulario)."""
        action = self.env.ref('hr_recruitment.action_hr_job_new_application')
        self.assertEqual(action.res_model, 'hr.applicant')
        self.assertIn('default_job_id', action.context,
                      'El botón debe precargar el puesto activo.')
        self.assertIn('active_id', action.context)

    def test_vistas_bca_exponen_boton_a_reclutadora(self) -> None:
        """Las vistas BCA exponen el alta a la Reclutadora y acotan a Encargado
        los items que exigen ACL/escritura."""
        kanban = self.env.ref('BCA_Seguros.view_hr_job_kanban_bca')
        arch_kanban = str(kanban.arch_db)
        self.assertIn('BCA_Seguros.group_bca_reclutadora', arch_kanban,
                      'El menú de tarjeta debe exponerse a la Reclutadora.')
        # Trackers y color/editar/archivar quedan restringidos a Encargado.
        self.assertEqual(arch_kanban.count('hr_recruitment.group_hr_recruitment_user'), 3,
                         'user + Trackers + settings deben restringirse a Encargado.')

        form = self.env.ref('BCA_Seguros.view_hr_job_form_bca')
        arch_form = str(form.arch_db)
        self.assertIn('BCA_Seguros.group_bca_reclutadora', arch_form)
        self.assertIn('Nuevo Postulante', arch_form)
        # El botón llama a la acción nativa precargadora (el ref %()d se
        # resuelve al id de la acción en el arch cargado).
        accion = self.env.ref('hr_recruitment.action_hr_job_new_application')
        self.assertIn(f'name="{accion.id}"', arch_form,
                      'El botón stat debe llamar a la acción nativa precargadora.')