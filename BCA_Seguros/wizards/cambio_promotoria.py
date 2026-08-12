from __future__ import annotations

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class BcaWizardCambioPromotoria(models.TransientModel):
    _name = 'bca.wizard.cambio.promotoria'
    _description = 'Cambiar Promotoría de Agente'

    agente_id: int = fields.Many2one(
        'res.partner',
        string='Agente',
        required=True,
        readonly=True,
        domain=[('bca_tipo', '=', 'agente')],
    )
    promotoria_actual_id: int = fields.Many2one(
        'res.partner',
        string='Promotoría Actual',
        related='agente_id.parent_id',
        readonly=True,
    )
    promotoria_nueva_id: int = fields.Many2one(
        'res.partner',
        string='Nueva Promotoría',
        required=True,
        domain=[('bca_tipo', '=', 'promotoria')],
    )
    fecha_cambio: fields.Date = fields.Date(
        string='Fecha Efectiva',
        required=True,
        default=fields.Date.context_today,
    )
    motivo: str = fields.Char(string='Motivo', required=True)
    polizas_afectadas: int = fields.Integer(
        string='Pólizas Afectadas',
        compute='_compute_impacto',
    )
    recibos_pendientes: int = fields.Integer(
        string='Recibos Pendientes',
        compute='_compute_impacto',
    )
    recibos_pagados: int = fields.Integer(
        string='Recibos Pagados',
        compute='_compute_impacto',
    )

    def _compute_impacto(self) -> None:
        for wizard in self:
            if not wizard.agente_id:
                wizard.polizas_afectadas = 0
                wizard.recibos_pendientes = 0
                wizard.recibos_pagados = 0
                continue
            polizas = self.env['bca.poliza'].search([
                ('agente_id', '=', wizard.agente_id.id),
            ])
            recibos = self.env['bca.recibo'].search([
                ('poliza_id.agente_id', '=', wizard.agente_id.id),
            ])
            wizard.polizas_afectadas = len(polizas)
            wizard.recibos_pendientes = len(recibos.filtered(
                lambda recibo: recibo.estado == 'pendiente'
            ))
            wizard.recibos_pagados = len(recibos.filtered(
                lambda recibo: recibo.estado == 'pagado'
            ))

    def action_confirmar(self) -> dict:
        self.ensure_one()
        if not (self.env.user.has_group('BCA_Seguros.group_bca_director_comercial')
                or self.env.user.has_group('BCA_Seguros.group_bca_director')):
            raise AccessError(
                _('Solo Director Comercial o Director pueden cambiar la Promotoría.')
            )
        if self.agente_id.bca_tipo != 'agente':
            raise ValidationError(_('El contacto seleccionado no es un Agente BCA.'))
        if not self.agente_id.parent_id:
            raise UserError(_('El Agente no tiene una Promotoría actual válida.'))
        if self.promotoria_nueva_id == self.promotoria_actual_id:
            raise ValidationError(_('La nueva Promotoría debe ser diferente de la actual.'))
        if self.promotoria_nueva_id.bca_tipo != 'promotoria':
            raise ValidationError(_('La nueva entidad debe ser una Promotoría BCA.'))
        if not self.promotoria_nueva_id.parent_id or \
                self.promotoria_nueva_id.parent_id.bca_tipo != 'holding':
            raise ValidationError(_('La nueva Promotoría debe pertenecer a un Holding BCA.'))
        if not self.motivo.strip():
            raise ValidationError(_('El motivo del cambio es obligatorio.'))

        self.agente_id.cambiar_promotoria(
            self.promotoria_nueva_id,
            self.fecha_cambio,
            self.motivo,
        )
        return {'type': 'ir.actions.act_window_close'}