from __future__ import annotations

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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

    def write(self, vals: dict) -> bool:
        """Detecta paso a stage hired y dispara creación de res.partner BCA.

        Solo cuando stage_id cambia a uno con hired_stage=True. Idempotente:
        si el applicant ya tiene partner_id asignado por este flujo, no recrea.
        """
        result = super().write(vals)
        if 'stage_id' in vals:
            for applicant in self:
                if applicant.stage_id and applicant.stage_id.hired_stage:
                    applicant._bca_crear_partner_desde_contratado()
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
