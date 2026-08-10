from __future__ import annotations

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class BcaAgenteCambioPromotoria(models.Model):
    """Immutable audit trail for an agent's network affiliation changes."""

    _name = 'bca.agente.cambio.promotoria'
    _description = 'Cambio de Promotoría de Agente'
    _order = 'fecha_cambio desc, id desc'

    agente_id: int = fields.Many2one(
        'res.partner',
        string='Agente',
        required=True,
        readonly=True,
        ondelete='restrict',
        index=True,
        domain=[('bca_tipo', '=', 'agente')],
    )
    promotoria_anterior_id: int = fields.Many2one(
        'res.partner',
        string='Promotoría Anterior',
        readonly=True,
        ondelete='restrict',
        index=True,
    )
    promotoria_nueva_id: int = fields.Many2one(
        'res.partner',
        string='Promotoría Nueva',
        required=True,
        readonly=True,
        ondelete='restrict',
        index=True,
        domain=[('bca_tipo', '=', 'promotoria')],
    )
    fecha_cambio: fields.Date = fields.Date(
        string='Fecha del Cambio',
        required=True,
        readonly=True,
        default=fields.Date.context_today,
    )
    motivo: str = fields.Char(string='Motivo', required=True, readonly=True)
    usuario_id: int = fields.Many2one(
        'res.users',
        string='Autorizado por',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
        ondelete='restrict',
    )
    fecha_registro: fields.Datetime = fields.Datetime(
        string='Registrado el',
        required=True,
        readonly=True,
        default=fields.Datetime.now,
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('bca_from_cambio_promotoria'):
            raise AccessError(
                _('Los cambios de Promotoría solo pueden registrarse mediante '
                  'el flujo autorizado.')
            )
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(_('El historial de cambios de Promotoría es inmutable.'))

    def unlink(self):
        raise AccessError(_('El historial de cambios de Promotoría es inmutable.'))