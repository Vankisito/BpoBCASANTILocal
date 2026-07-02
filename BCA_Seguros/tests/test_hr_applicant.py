from __future__ import annotations

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
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

    # ---------------------------------------------------------------
    # Etapa 12 Fase A — cimientos (HU-1.0/1.1/1.2)
    # ---------------------------------------------------------------
    def test_embudo_12_etapas_cargadas(self) -> None:
        """Las 12 etapas comerciales + Alta Interna cargan como datos del módulo."""
        Stage = self.env['hr.recruitment.stage']
        job_recl = self.job_reclutamiento
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

    def test_hired_stages_flag(self) -> None:
        """Cédula Emitida y Alta Interna tienen hired_stage=True; el resto no."""
        cedula = self.env.ref('BCA_Seguros.stage_cedula_emitida')
        alta = self.env.ref('BCA_Seguros.stage_alta_interna')
        recibido = self.env.ref('BCA_Seguros.stage_recibido')
        self.assertTrue(cedula.hired_stage, 'Cédula Emitida debe ser hired_stage.')
        self.assertTrue(alta.hired_stage, 'Alta Interna debe ser hired_stage.')
        self.assertFalse(recibido.hired_stage, 'Recibido NO debe ser hired_stage.')
        # Alta Interna es global (sin job_ids): disponible a jobs internos.
        self.assertFalse(alta.job_ids, 'Alta Interna debe ser global (sin job_ids).')

    def test_campos_identificacion_capturables(self) -> None:
        """Los campos bca_ de identificación/perfil se capturan y persisten."""
        sede = self.env['bca.sede'].create({'name': 'Sede Test', 'codigo': 'TST'})
        applicant = self._crear_applicant(
            self.job_reclutamiento,
            bca_sede_id=sede.id,
            bca_ramo='vida',
            bca_genero='femenino',
            bca_institucion='Universidad X',
            bca_perfil_academico='Licenciatura',
            bca_perfil_laboral='Ventas',
            bca_tiene_cedula_previa=True,
            bca_tipo_candidato='Referido',
            bca_referido_por='Ana',
            bca_folio_cv='CV-001',
            bca_evento='Feria de Empleo',
            bca_contactado=True,
            bca_entrevistado=False,
            bca_reagendaciones=2,
        )
        self.assertEqual(applicant.bca_sede_id, sede)
        self.assertEqual(applicant.bca_ramo, 'vida')
        self.assertEqual(applicant.bca_genero, 'femenino')
        self.assertEqual(applicant.bca_reagendaciones, 2)
        self.assertEqual(applicant.bca_evento, 'Feria de Empleo')

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
        # No se reinventan campos que ya existen de forma nativa.
        for redundante in ('bca_rfc', 'bca_nombre', 'bca_correo', 'bca_telefono'):
            self.assertNotIn(redundante, fields,
                             f'{redundante} duplica un campo nativo; debe reusarse.')
        # Los campos nativos reusados existen.
        for nativo in ('partner_name', 'email_from', 'partner_phone'):
            self.assertIn(nativo, fields, f'Se esperaba reusar el campo nativo {nativo}.')
