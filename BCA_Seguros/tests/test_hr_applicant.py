from __future__ import annotations

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.BCA_Seguros.models.product_template import RAMO_SELECTION
from odoo.addons.BCA_Seguros.models.res_partner import GENERO_SELECTION


@tagged('BCA_Seguros')
class TestHrApplicant(TransactionCase):
    """Etapa 3 + Etapa 12 Fase A — hr.applicant: campos BCA y conversión."""

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
        cls.aseguradora = cls.env['res.partner'].create({
            'name': 'Aseguradora Test',
            'bca_tipo': 'aseguradora',
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

    def _datos_habilitacion(self, **overrides) -> dict:
        """Los 5 datos de habilitación (Fase C) + promotoría destino."""
        vals = {
            'bca_promotoria_destino_id': self.promotoria.id,
            'bca_clave_arranque': 'CLV-001',
            'bca_fecha_cedula': date(2026, 1, 15),
            'bca_aseguradora_id': self.aseguradora.id,
            'bca_rfc': 'AGEJ800101ABC',
            'bca_curp': 'AGEJ800101HDFxxx01',
        }
        vals.update(overrides)
        return vals

    def test_contratado_reclutamiento_crea_agente(self) -> None:
        """Reclutamiento con los 5 datos → crea agente + puente + empleado."""
        applicant = self._crear_applicant(
            self.job_reclutamiento,
            partner_name='Juan Agente',
            **self._datos_habilitacion(),
        )
        applicant.stage_id = self.stage_hired
        agente = applicant.partner_id
        self.assertTrue(agente, 'Debe crearse partner_id.')
        self.assertEqual(agente.bca_tipo, 'agente')
        self.assertEqual(agente.parent_id, self.promotoria)
        self.assertEqual(agente.name, 'Juan Agente')
        # RFC → vat nativo; CURP → bca_curp.
        self.assertEqual(agente.vat, 'AGEJ800101ABC')
        self.assertEqual(agente.bca_curp, 'AGEJ800101HDFxxx01')

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

    def test_promotoria_hired_en_cedula_emitida_crea_promotoria(self) -> None:
        """D-20: la promotoría comparte el embudo comercial; al llegar a la etapa
        hired real "Cédula Emitida" se crea el res.partner promotoría (ruteo por job)."""
        cedula = self.env.ref('BCA_Seguros.stage_cedula_emitida')
        self.assertIn(self.job_captacion, cedula.job_ids,
                      'La promotoría debe ver la etapa "Cédula Emitida".')
        applicant = self._crear_applicant(
            self.job_captacion, partner_name='Promotoría Embudo SA',
        )
        applicant.stage_id = cedula
        self.assertTrue(applicant.partner_id)
        self.assertEqual(applicant.partner_id.bca_tipo, 'promotoria')
        self.assertEqual(applicant.partner_id.parent_id, self.holding)

    def test_reclutamiento_sin_promotoria_destino_error(self) -> None:
        """Reclutamiento con 5 datos pero sin promotoría destino → UserError."""
        datos = self._datos_habilitacion(bca_promotoria_destino_id=False)
        applicant = self._crear_applicant(self.job_reclutamiento, **datos)
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

    # ---------------------------------------------------------------
    # Etapa 12 Fase A — cimientos (HU-1.0/1.1/1.2)
    # ---------------------------------------------------------------
    def test_embudo_12_etapas_cargadas(self) -> None:
        """Las 12 etapas comerciales cargan scopeadas a AMBOS jobs comerciales (D-20)."""
        job_recl = self.job_reclutamiento
        job_capt = self.job_captacion
        xmlids_seq = [
            ('stage_recibido', 1), ('stage_prospeccion', 2), ('stage_cafe', 3),
            ('stage_entrevista', 4), ('stage_evaluacion_pda', 5),
            ('stage_acuerdo_arranque', 6), ('stage_clave_arranque', 7),
            ('stage_inscripcion_cia', 8), ('stage_curso_cedula', 9),
            ('stage_examen', 10), ('stage_cedula_emitida', 11),
            ('stage_en_desarrollo', 12),
        ]
        for xmlid, seq in xmlids_seq:
            stage = self.env.ref(f'BCA_Seguros.{xmlid}')
            self.assertEqual(stage.sequence, seq, f'{xmlid} sequence != {seq}')
            self.assertIn(job_recl, stage.job_ids,
                          f'{xmlid} debe estar scopeada a job_reclutamiento_agente.')
            self.assertIn(job_capt, stage.job_ids,
                          f'{xmlid} debe estar scopeada a job_captacion_promotoria.')

    def test_hired_stages_flag(self) -> None:
        """Cédula Emitida es la etapa hired del embudo comercial; Recibido no lo es."""
        cedula = self.env.ref('BCA_Seguros.stage_cedula_emitida')
        recibido = self.env.ref('BCA_Seguros.stage_recibido')
        self.assertTrue(cedula.hired_stage, 'Cédula Emitida debe ser hired_stage.')
        self.assertFalse(recibido.hired_stage, 'Recibido NO debe ser hired_stage.')
        # D-20: la etapa hired del embudo aplica a ambas figuras comerciales.
        self.assertIn(self.job_reclutamiento, cedula.job_ids)
        self.assertIn(self.job_captacion, cedula.job_ids)
        # La etapa BCA "Contratado (Alta Interna)" fue retirada (embudo nativo).
        self.assertFalse(
            self.env.ref('BCA_Seguros.stage_alta_interna', raise_if_not_found=False),
            'stage_alta_interna debe estar retirada (D-20).',
        )

    def test_campos_identificacion_capturables(self) -> None:
        """Los campos bca_ de identificación/perfil se capturan y persisten.

        Tras D-19: académico=type_id nativo, origen=UTM nativo, seguimiento=embudo;
        se conservan folio_cv (Identificación) y ramo/perfil_laboral/tipo (Detalles).
        """
        sede = self.env['bca.sede'].create({'name': 'Sede Test', 'codigo': 'TST'})
        applicant = self._crear_applicant(
            self.job_reclutamiento,
            bca_sede_id=sede.id,
            bca_ramo='vida',
            bca_genero='femenino',
            bca_institucion='Universidad X',
            bca_perfil_laboral='Ventas',
            bca_tipo_candidato='Referido',
            bca_folio_cv='CV-001',
        )
        self.assertEqual(applicant.bca_sede_id, sede)
        self.assertEqual(applicant.bca_ramo, 'vida')
        self.assertEqual(applicant.bca_genero, 'femenino')
        self.assertEqual(applicant.bca_perfil_laboral, 'Ventas')
        self.assertEqual(applicant.bca_tipo_candidato, 'Referido')
        self.assertEqual(applicant.bca_folio_cv, 'CV-001')

    def test_edad_computed_no_almacenada(self) -> None:
        """bca_edad se calcula desde la fecha de nacimiento y NO se almacena."""
        nacimiento = date.today() - relativedelta(years=30)
        applicant = self._crear_applicant(
            self.job_reclutamiento,
            bca_fecha_nacimiento=nacimiento,
        )
        self.assertEqual(applicant.bca_edad, 30)
        self.assertFalse(
            self.env['hr.applicant']._fields['bca_edad'].store,
            'bca_edad debe ser computed no almacenado (depende de hoy).',
        )
        # Sin fecha de nacimiento → 0.
        vacio = self._crear_applicant(self.job_reclutamiento)
        self.assertEqual(vacio.bca_edad, 0)

    def test_no_campos_duplicados(self) -> None:
        """Reuso, no reinvención: género/ramo reusan selecciones; sin campos RFC/nombre duplicados."""
        fields = self.env['hr.applicant']._fields
        # Género/ramo reusan exactamente las selecciones compartidas.
        self.assertEqual(fields['bca_genero'].selection, GENERO_SELECTION)
        self.assertEqual(fields['bca_ramo'].selection, RAMO_SELECTION)
        # No se reinventan campos que ya existen de forma nativa en hr.applicant.
        for redundante in ('bca_nombre', 'bca_correo', 'bca_telefono'):
            self.assertNotIn(redundante, fields,
                             f'{redundante} duplica un campo nativo; debe reusarse.')
        # Los campos nativos reusados existen.
        for nativo in ('partner_name', 'email_from', 'partner_phone'):
            self.assertIn(nativo, fields, f'Se esperaba reusar el campo nativo {nativo}.')
        # RFC: en res.partner se reusa el `vat` nativo (NO se crea bca_rfc en el
        # partner). En hr.applicant sí existe bca_rfc (no hay `vat` nativo ahí).
        partner_fields = self.env['res.partner']._fields
        self.assertIn('vat', partner_fields)
        self.assertNotIn('bca_rfc', partner_fields,
                         'res.partner debe reusar `vat`, no crear bca_rfc.')
        self.assertIn('bca_rfc', fields,
                      'hr.applicant necesita bca_rfc (no tiene `vat` nativo).')

    # ---------------------------------------------------------------
    # Etapa 12 Fase B — PDA + compuerta de riesgo L1 (HU-1.3)
    # ---------------------------------------------------------------
    def _crear_applicant_pda(self, nivel: str, **overrides) -> object:
        return self._crear_applicant(
            self.job_reclutamiento,
            bca_promotoria_destino_id=self.promotoria.id,
            bca_pda_nivel=nivel,
            **overrides,
        )

    def test_pda_riesgo_computed(self) -> None:
        """Nivel baja/no_ideal ⇒ riesgo; ideal/recomendado/aceptable ⇒ sin riesgo."""
        for nivel in ('baja', 'no_ideal'):
            self.assertTrue(self._crear_applicant_pda(nivel).bca_pda_riesgo)
        for nivel in ('ideal', 'recomendado', 'aceptable'):
            self.assertFalse(self._crear_applicant_pda(nivel).bca_pda_riesgo)

    def test_pda_riesgo_crea_actividad_promotor(self) -> None:
        """Riesgo PDA sin VoBo ⇒ actividad "Visto bueno PDA requerido" al promotor."""
        promotor = self.env['res.users'].create({
            'name': 'Promotor Responsable',
            'login': 'promotor_pda@test.com',
            'partner_id': self.promotoria.id,
        })
        applicant = self._crear_applicant(
            self.job_reclutamiento,
            bca_promotoria_destino_id=self.promotoria.id,
        )
        applicant.bca_pda_nivel = 'baja'  # dispara notificación vía write
        actividades = applicant.activity_ids.filtered(
            lambda a: a.user_id == promotor)
        self.assertTrue(actividades, 'Debe crear actividad para el promotor.')
        self.assertEqual(actividades[0].summary, 'Visto bueno PDA requerido')
        # Idempotente: no duplica al reescribir.
        applicant.bca_pda_nivel = 'no_ideal'
        self.assertEqual(
            len(applicant.activity_ids.filtered(lambda a: a.user_id == promotor)),
            1, 'No debe duplicar la actividad del promotor.')

    def test_pda_avance_sin_vobo_bloquea(self) -> None:
        """Avanzar más allá de "Evaluación PDA" con riesgo y sin VoBo ⇒ ValidationError."""
        stage_acuerdo = self.env.ref('BCA_Seguros.stage_acuerdo_arranque')
        applicant = self._crear_applicant_pda('baja')
        with self.assertRaises(ValidationError):
            applicant.stage_id = stage_acuerdo

    def test_pda_con_vobo_avanza(self) -> None:
        """Con VoBo del promotor, el candidato en riesgo sí avanza."""
        stage_acuerdo = self.env.ref('BCA_Seguros.stage_acuerdo_arranque')
        applicant = self._crear_applicant_pda(
            'baja', bca_pda_visto_bueno_promotor=True)
        applicant.stage_id = stage_acuerdo  # no debe lanzar
        self.assertEqual(applicant.stage_id, stage_acuerdo)

    # ---------------------------------------------------------------
    # Etapa 12 Fase C — conversión en Cédula Emitida L2 (HU-1.4/1.5)
    # ---------------------------------------------------------------
    def test_hired_sin_5_datos_bloquea(self) -> None:
        """Llegar a una etapa hired sin los 5 datos ⇒ ValidationError (L2)."""
        applicant = self._crear_applicant(
            self.job_reclutamiento,
            bca_promotoria_destino_id=self.promotoria.id,
        )
        with self.assertRaises(ValidationError):
            applicant.stage_id = self.stage_hired

    def test_conversion_crea_puente_clave_arranque(self) -> None:
        """La conversión asienta el puente en estado clave_arranque (F1/D-14)."""
        applicant = self._crear_applicant(
            self.job_reclutamiento, partner_name='Ana Agente',
            **self._datos_habilitacion(),
        )
        applicant.stage_id = self.stage_hired
        claves = applicant.partner_id.agente_aseguradora_ids
        self.assertEqual(len(claves), 1)
        self.assertEqual(claves.estado, 'clave_arranque')
        self.assertNotEqual(claves.estado, 'clave_definitiva',
                            'El recién habilitado NO debe computar PCA.')
        self.assertEqual(claves.aseguradora_id, self.aseguradora)
        self.assertEqual(claves.clave_agente, 'CLV-001')

    def test_conversion_crea_employee(self) -> None:
        """La conversión crea un hr.employee vinculado por work_contact_id."""
        applicant = self._crear_applicant(
            self.job_reclutamiento, partner_name='Beto Agente',
            **self._datos_habilitacion(),
        )
        applicant.stage_id = self.stage_hired
        empleado = self.env['hr.employee'].search(
            [('work_contact_id', '=', applicant.partner_id.id)])
        self.assertEqual(len(empleado), 1)
        self.assertEqual(empleado.name, 'Beto Agente')

    def test_idempotencia_por_rfc_curp(self) -> None:
        """Mismo RFC+CURP en otra aseguradora ⇒ mismo agente, clave agregada (D-15)."""
        aseguradora2 = self.env['res.partner'].create({
            'name': 'Aseguradora Dos', 'bca_tipo': 'aseguradora',
        })
        app1 = self._crear_applicant(
            self.job_reclutamiento, partner_name='Caro Agente',
            **self._datos_habilitacion(),
        )
        app1.stage_id = self.stage_hired
        agente1 = app1.partner_id

        app2 = self._crear_applicant(
            self.job_reclutamiento, partner_name='Caro Agente',
            **self._datos_habilitacion(
                bca_aseguradora_id=aseguradora2.id, bca_clave_arranque='CLV-002'),
        )
        app2.stage_id = self.stage_hired
        self.assertEqual(app2.partner_id, agente1,
                         'Debe reutilizarse el mismo agente por Id interno.')
        self.assertEqual(len(agente1.agente_aseguradora_ids), 2,
                         'Se agrega la clave de la nueva aseguradora.')
        self.assertEqual(
            set(agente1.agente_aseguradora_ids.mapped('estado')), {'clave_arranque'})

    def test_job_interno_nativo_no_crea_puente_ni_agente(self) -> None:
        """Puesto interno (job no BCA) en etapa hired ⇒ sin partner agente ni puente.

        Los internos cierran por el embudo nativo (etapa hired nativa). El ruteo por
        job en _bca_crear_partner_desde_contratado no crea agente/promotoría (D-20).
        """
        antes = self.env['res.partner.agente.aseguradora'].search_count([])
        applicant = self._crear_applicant(self.job_estandar)
        applicant.stage_id = self.stage_hired
        if applicant.partner_id:
            self.assertNotEqual(applicant.partner_id.bca_tipo, 'agente')
        despues = self.env['res.partner.agente.aseguradora'].search_count([])
        self.assertEqual(antes, despues, 'El alta interna no debe crear puentes.')

    # ---------------------------------------------------------------
    # Etapa 12 Fase D — motivos de rechazo + automatización + SIC (HU-1.7/1.9)
    # ---------------------------------------------------------------
    def test_refuse_reasons_seed(self) -> None:
        """Los 2 motivos de rechazo están seed como datos del módulo."""
        prospecto = self.env.ref('BCA_Seguros.refuse_reason_declinado_prospecto')
        bca = self.env.ref('BCA_Seguros.refuse_reason_declinado_bca')
        self.assertEqual(prospecto.name, 'Declinado por Prospecto')
        self.assertEqual(bca.name, 'Declinado por BCA')

    def test_automation_aviso_etapa_seed(self) -> None:
        """La automatización de aviso por etapa (L6) está seed y activa."""
        automation = self.env.ref('BCA_Seguros.automation_aviso_cambio_etapa')
        self.assertEqual(automation.trigger, 'on_stage_set')
        self.assertEqual(automation.model_id.model, 'hr.applicant')
        self.assertTrue(automation.action_server_ids, 'Debe tener acción servidor.')

    def test_sic_action_pivote_seed(self) -> None:
        """La acción SIC de reclutamiento abre pivote sobre hr.applicant."""
        action = self.env.ref('BCA_Seguros.action_sic_reclutamiento')
        self.assertEqual(action.res_model, 'hr.applicant')
        self.assertIn('pivot', action.view_mode)
