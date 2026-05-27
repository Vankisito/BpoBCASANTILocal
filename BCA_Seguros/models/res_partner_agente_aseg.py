from __future__ import annotations

from odoo import fields, models


class ResPartnerAgenteAseguradora(models.Model):
    _name = 'res.partner.agente.aseguradora'
    _description = 'Clave de Agente por Aseguradora'
    _rec_name = 'clave_agente'

    agente_id: int = fields.Many2one(
        'res.partner',
        string='Agente',
        required=True,
        ondelete='cascade',
        domain=[('bca_tipo', '=', 'agente')],
        index=True,
    )
    aseguradora_id: int = fields.Many2one(
        'res.partner',
        string='Aseguradora',
        required=True,
        ondelete='restrict',
        domain=[('bca_tipo', '=', 'aseguradora')],
        index=True,
    )
    clave_agente: str = fields.Char(string='Clave Agente', required=True)
    estado: str = fields.Selection(
        [('prospecto', 'Prospecto'), ('con_licencia', 'Con Licencia')],
        string='Estado',
        required=True,
    )
    fecha_licencia: fields.Date = fields.Date(string='Fecha de Licencia')

    # v19: models.Constraint() reemplaza _sql_constraints (deprecated en v19)
    _unique_clave_aseg = models.Constraint(
        'UNIQUE(aseguradora_id, clave_agente)',
        'La clave del agente debe ser única por aseguradora',
    )
    _unique_agente_aseg = models.Constraint(
        'UNIQUE(agente_id, aseguradora_id)',
        'Un agente solo puede registrarse una vez por aseguradora',
    )
