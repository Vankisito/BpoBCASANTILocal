from __future__ import annotations

from odoo import api, fields, models


class HrEmployee(models.Model):
    """Espejo de solo lectura de la pestaña "BCA Seguros" del contacto.

    El empleado está vinculado a su contacto agente vía ``work_contact_id``
    (ver ``_bca_crear_empleado`` en hr_applicant.py). Esta extensión expone los
    campos BCA de ese contacto en la ficha de empleado sin duplicar la fuente
    de verdad: todo es ``related`` read-only (el contacto sigue siendo el único
    lugar de edición).

    Prefijo ``bca_`` en TODOS los campos espejo: varios nombres nativos de
    ``hr.employee`` colisionan (``parent_id`` = manager, ``country_id`` =
    ciudadanía) y no se deben pisar.
    """

    _inherit = 'hr.employee'

    # -- Identidad BCA (espejo de res.partner) -----------------------------
    bca_tipo: str = fields.Selection(
        related='work_contact_id.bca_tipo',
        readonly=True,
    )
    # Promotoría: espejo de parent_id del contacto (el parent_id de hr.employee
    # es el manager, NO se toca).
    bca_parent_id: int = fields.Many2one(
        'res.partner',
        string='Promotoría (Contácto)',
        related='work_contact_id.parent_id',
        readonly=True,
    )
    bca_codigo_aseguradora: str = fields.Char(
        string='Código Aseguradora',
        related='work_contact_id.bca_codigo_aseguradora',
        readonly=True,
    )
    bca_promotoria_id: int = fields.Many2one(
        'res.partner',
        string='Promotoría',
        related='work_contact_id.bca_promotoria_id',
        readonly=True,
    )
    bca_estado_agente: str = fields.Selection(
        related='work_contact_id.bca_estado_agente',
        readonly=True,
    )
    bca_es_contratante: bool = fields.Boolean(
        string='Es Contratante',
        related='work_contact_id.bca_es_contratante',
        readonly=True,
    )
    bca_es_asegurado: bool = fields.Boolean(
        string='Es Asegurado',
        related='work_contact_id.bca_es_asegurado',
        readonly=True,
    )

    # -- Datos demográficos -------------------------------------------------
    bca_fecha_nacimiento: fields.Date = fields.Date(
        string='Fecha de Nacimiento',
        related='work_contact_id.bca_fecha_nacimiento',
        readonly=True,
    )
    bca_estado_civil: str = fields.Selection(
        related='work_contact_id.bca_estado_civil',
        readonly=True,
    )
    bca_genero: str = fields.Selection(
        related='work_contact_id.bca_genero',
        readonly=True,
    )
    bca_curp: str = fields.Char(
        string='CURP',
        related='work_contact_id.bca_curp',
        readonly=True,
    )

    # -- Claves por Aseguradora --------------------------------------------
    # One2many no se espeja con `related` (Odoo lo rechaza). Se vuelca como
    # Many2many computed read-only; la edición sigue viviendo en el contacto.
    bca_claves_aseguradora_ids: list[int] = fields.Many2many(
        'res.partner.agente.aseguradora',
        string='Claves por Aseguradora',
        compute='_compute_bca_claves_aseguradora',
        readonly=True,
    )

    @api.depends('work_contact_id')
    def _compute_bca_claves_aseguradora(self) -> None:
        for rec in self:
            rec.bca_claves_aseguradora_ids = (
                rec.work_contact_id.agente_aseguradora_ids
            )

    def action_bca_open_contact(self) -> dict:
        """Abre la ficha de contacto vinculado (única fuente de edición)."""
        self.ensure_one()
        if not self.work_contact_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'hr.employee',
                'view_mode': 'form',
                'res_id': self.id,
            }
        return {
            'type': 'ir.actions.act_window',
            'name': self.work_contact_id.display_name,
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.work_contact_id.id,
        }
