from __future__ import annotations

import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .product_template import RAMO_SELECTION
from .res_partner import GENERO_SELECTION

_logger = logging.getLogger(__name__)

# Niveles de compatibilidad PDA (Etapa 12 Fase B, HU-1.3). Constante de módulo
# (patrón del proyecto). Los niveles 'no_ideal' y 'baja' marcan riesgo y activan
# la compuerta L1 (requieren visto bueno del promotor para avanzar).
PDA_NIVEL_SELECTION = [
    ('ideal', 'Ideal'),
    ('recomendado', 'Recomendado'),
    ('aceptable', 'Aceptable'),
    ('no_ideal', 'No Ideal'),
    ('baja', 'Baja Compatibilidad'),
]
_PDA_NIVELES_RIESGO = ('no_ideal', 'baja')


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    bca_promotoria_destino_id: int = fields.Many2one(
        'res.partner',
        string='Promotoría destino',
        domain=[('bca_tipo', '=', 'promotoria')],
        help='Promotoría a la que se afiliará el agente al ser contratado. '
             'Requerido cuando el puesto es "Reclutamiento de Agente".',
        tracking=True,
    )

    # --- Identificación / perfil del candidato (Etapa 12 Fase A, HU-1.2) ---
    # Campos de captura sin lógica. RFC → campo estándar `vat`; nombre →
    # partner_name; teléfono → partner_phone; correo → email_from (se reusan,
    # no se redefinen). Género/ramo reusan las selecciones ya existentes.
    bca_sede_id: int = fields.Many2one(
        'bca.sede',
        string='Sede / Plaza',
        ondelete='set null',
        help='Plaza donde se recluta al candidato.',
    )
    bca_ramo: str = fields.Selection(RAMO_SELECTION, string='Ramo')
    bca_genero: str = fields.Selection(GENERO_SELECTION, string='Género')
    bca_fecha_nacimiento: fields.Date = fields.Date(string='Fecha de Nacimiento')
    bca_edad: int = fields.Integer(
        string='Edad',
        compute='_compute_bca_edad',
        store=False,
        help='Edad calculada a la fecha actual desde la fecha de nacimiento. '
             'No se almacena (cambia con el tiempo); para segmentar por edad '
             'en reportes use rangos de fecha de nacimiento.',
    )
    bca_institucion: str = fields.Char(string='Institución')
    bca_perfil_academico: str = fields.Char(string='Perfil Académico')
    bca_perfil_laboral: str = fields.Char(string='Perfil Laboral')
    bca_tiene_cedula_previa: bool = fields.Boolean(string='¿Tiene Cédula Previa?')
    bca_tipo_candidato: str = fields.Char(string='Tipo de Candidato')
    bca_referido_por: str = fields.Char(string='Referido Por')
    bca_folio_cv: str = fields.Char(string='Folio CV', copy=False)
    # SI-3: "Evento" (efectividad) como campo de texto simple; el modelo
    # relacional bca.evento queda como mejora futura (D-16).
    bca_evento: str = fields.Char(string='Evento')
    bca_contactado: bool = fields.Boolean(string='Contactado')
    bca_entrevistado: bool = fields.Boolean(string='Entrevistado')
    bca_reagendaciones: int = fields.Integer(string='Reagendaciones', default=0)

    @api.depends('bca_fecha_nacimiento')
    def _compute_bca_edad(self) -> None:
        """Edad a la fecha actual. No almacenado: se recalcula en cada lectura."""
        today = fields.Date.context_today(self)
        for applicant in self:
            if applicant.bca_fecha_nacimiento:
                applicant.bca_edad = relativedelta(
                    today, applicant.bca_fecha_nacimiento,
                ).years
            else:
                applicant.bca_edad = 0

    # --- Evaluación PDA + compuerta de riesgo L1 (Etapa 12 Fase B, HU-1.3) ---
    bca_pda_nivel: str = fields.Selection(
        PDA_NIVEL_SELECTION, string='Nivel PDA', copy=False,
    )
    bca_pda_correlacion: float = fields.Float(string='Correlación PDA', copy=False)
    bca_pda_perfil: str = fields.Char(string='Perfil PDA', copy=False)
    bca_pda_visto_bueno_promotor: bool = fields.Boolean(
        string='Visto Bueno del Promotor', copy=False,
        help='El promotor autoriza avanzar pese al nivel PDA de riesgo.',
    )
    bca_pda_riesgo: bool = fields.Boolean(
        string='PDA en Riesgo',
        compute='_compute_bca_pda_riesgo',
        store=True,
        copy=False,
        help='Verdadero cuando el nivel PDA es "No Ideal" o "Baja Compatibilidad". '
             'Bloquea avanzar más allá de "Evaluación PDA" sin visto bueno (L1).',
    )

    @api.depends('bca_pda_nivel')
    def _compute_bca_pda_riesgo(self) -> None:
        """Riesgo PDA: niveles no_ideal / baja."""
        for applicant in self:
            applicant.bca_pda_riesgo = applicant.bca_pda_nivel in _PDA_NIVELES_RIESGO

    @api.constrains('stage_id', 'bca_pda_riesgo', 'bca_pda_visto_bueno_promotor')
    def _check_pda_gate(self) -> None:
        """L1: bloquea avanzar más allá de "Evaluación PDA" con riesgo sin VoBo.

        Solo aplica al embudo de reclutamiento de agentes. La etapa de corte se
        resuelve por `env.ref` y se compara por `sequence` (nunca por ID: D-13).
        """
        job_recl = self.env.ref(
            'BCA_Seguros.job_reclutamiento_agente', raise_if_not_found=False,
        )
        stage_pda = self.env.ref(
            'BCA_Seguros.stage_evaluacion_pda', raise_if_not_found=False,
        )
        if not job_recl or not stage_pda:
            return
        for applicant in self:
            if applicant.job_id != job_recl or not applicant.stage_id:
                continue
            if applicant.stage_id.sequence <= stage_pda.sequence:
                continue
            if applicant.bca_pda_riesgo and not applicant.bca_pda_visto_bueno_promotor:
                raise ValidationError(_(
                    'El candidato "%s" tiene un nivel PDA de riesgo y no puede '
                    'avanzar más allá de "Evaluación PDA" sin el visto bueno del '
                    'promotor de la promotoría destino.'
                ) % (applicant.partner_name or applicant.display_name))

    def _bca_notificar_riesgo_pda(self) -> None:
        """Al activarse el riesgo PDA sin VoBo, crea actividad para el promotor.

        SI-2: el promotor solo recibe la notificación. Idempotente: no duplica la
        actividad si ya existe una abierta para el mismo usuario.
        """
        self.ensure_one()
        job_recl = self.env.ref(
            'BCA_Seguros.job_reclutamiento_agente', raise_if_not_found=False,
        )
        if self.job_id != job_recl:
            return
        if not (self.bca_pda_riesgo and not self.bca_pda_visto_bueno_promotor):
            return
        if not self.bca_promotoria_destino_id:
            return
        # Promotor = usuario ligado a la promotoría; fallback a la reclutadora.
        promotor_user = self.bca_promotoria_destino_id.user_ids[:1] or self.user_id
        if not promotor_user:
            return
        summary = _('Visto bueno PDA requerido')
        ya_existe = self.activity_ids.filtered(
            lambda a: a.summary == summary and a.user_id == promotor_user,
        )
        if ya_existe:
            return
        nivel_label = dict(self._fields['bca_pda_nivel'].selection).get(
            self.bca_pda_nivel, self.bca_pda_nivel or '',
        )
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=summary,
            note=_('El candidato tiene un nivel PDA de riesgo (%s). Se requiere '
                   'su visto bueno para que avance en el embudo.') % nivel_label,
            user_id=promotor_user.id,
        )

    def write(self, vals: dict) -> bool:
        """Detecta paso a stage hired y dispara creación de res.partner BCA.

        Solo cuando stage_id cambia a uno con hired_stage=True. Idempotente:
        si el applicant ya tiene partner_id asignado por este flujo, no recrea.
        También notifica al promotor cuando la evaluación PDA marca riesgo (L1).
        """
        result = super().write(vals)
        if 'stage_id' in vals:
            for applicant in self:
                if applicant.stage_id and applicant.stage_id.hired_stage:
                    applicant._bca_crear_partner_desde_contratado()
        if {'bca_pda_nivel', 'bca_pda_visto_bueno_promotor'} & vals.keys():
            for applicant in self:
                applicant._bca_notificar_riesgo_pda()
        return result

    def _bca_crear_partner_desde_contratado(self) -> None:
        """Crea res.partner agente o promotoría según el hr.job del applicant.

        Idempotente: si ya hay partner_id con bca_tipo coherente, no hace nada.
        Solo actúa sobre applicants cuyo job_id es uno de los dos BCA registrados;
        ignora silenciosamente cualquier otro job (ej. puestos estándar de RH).
        """
        self.ensure_one()
        job_captacion = self.env.ref(
            'BCA_Seguros.job_captacion_promotoria', raise_if_not_found=False,
        )
        job_reclutamiento = self.env.ref(
            'BCA_Seguros.job_reclutamiento_agente', raise_if_not_found=False,
        )

        if not self.job_id or self.job_id not in (job_captacion, job_reclutamiento):
            return

        if self.partner_id and self.partner_id.bca_tipo in ('promotoria', 'agente'):
            _logger.info(
                'hr.applicant %s ya tiene partner BCA (%s); no se recrea.',
                self.id, self.partner_id.id,
            )
            return

        partner_vals = {
            'name': self.partner_name or self.name,
            'email': self.email_from or False,
            'phone': self.partner_phone or False,
        }

        if self.job_id == job_captacion:
            holding = self.env.ref(
                'BCA_Seguros.partner_bca_holding', raise_if_not_found=False,
            )
            if not holding:
                raise UserError(_(
                    'No se encontró el partner Grupo BCA holding '
                    '(BCA_Seguros.partner_bca_holding). Verifique que '
                    'data/aseguradoras_iniciales.xml esté cargado.'
                ))
            partner_vals.update({
                'bca_tipo': 'promotoria',
                'parent_id': holding.id,
                'is_company': True,
            })
        else:  # job_reclutamiento
            if not self.bca_promotoria_destino_id:
                raise UserError(_(
                    'Para contratar a un agente debe especificar la '
                    'Promotoría destino en el candidato.'
                ))
            partner_vals.update({
                'bca_tipo': 'agente',
                'parent_id': self.bca_promotoria_destino_id.id,
                'is_company': False,
            })

        partner = self.env['res.partner'].create(partner_vals)
        self.partner_id = partner
        self.message_post(body=_(
            'Se creó automáticamente el contacto BCA <a href="#" data-oe-model="res.partner" '
            'data-oe-id="%(id)s">%(name)s</a> (%(tipo)s) al cerrar el candidato como Contratado.'
        ) % {'id': partner.id, 'name': partner.name, 'tipo': partner.bca_tipo})
        _logger.info(
            'hr.applicant %s: creado res.partner %s (%s, bca_tipo=%s).',
            self.id, partner.id, partner.name, partner.bca_tipo,
        )
