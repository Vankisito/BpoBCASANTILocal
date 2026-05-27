from __future__ import annotations

from odoo import api, fields, models
from odoo.exceptions import ValidationError

TIPO_SELECTION = [
    ('holding', 'Holding'),
    ('aseguradora', 'Aseguradora'),
    ('promotoria', 'Promotoría'),
    ('agente', 'Agente'),
    ('contratante', 'Contratante'),
]
ESTADO_AGENTE_SELECTION = [
    ('prospecto', 'Prospecto'),
    ('con_licencia', 'Con Licencia'),
]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    bca_tipo: str = fields.Selection(
        TIPO_SELECTION,
        string='Tipo BCA',
        index=True,
    )
    bca_estado_agente: str = fields.Selection(
        ESTADO_AGENTE_SELECTION,
        string='Estado Agente',
        index=True,
    )
    bca_fecha_licencia: fields.Date = fields.Date(string='Fecha de Licencia')
    bca_codigo_aseguradora: str = fields.Char(
        string='Código Aseguradora',
        index=True,
    )

    agente_aseguradora_ids: list[int] = fields.One2many(
        'res.partner.agente.aseguradora',
        'agente_id',
        string='Claves por Aseguradora',
    )

    # C2: computed SIN store — retorna parent_id en tiempo real, nunca stale data.
    # search= permite filtrabilidad desde domain y search_read de la API.
    bca_promotoria_id: int = fields.Many2one(
        'res.partner',
        string='Promotoría',
        compute='_compute_promotoria_id',
        store=False,
        search='_search_promotoria_id',
    )
    bca_categoria_id: int = fields.Many2one(
        'res.partner.category',
        string='Categoría BCA',
        compute='_compute_categoria_id',
    )

    @api.depends('bca_tipo', 'parent_id')
    def _compute_promotoria_id(self) -> None:
        for rec in self:
            rec.bca_promotoria_id = rec.parent_id if rec.bca_tipo == 'agente' else False

    def _search_promotoria_id(self, operator: str, value: object) -> list:
        return [('parent_id', operator, value)]

    @api.depends('bca_tipo')
    def _compute_categoria_id(self) -> None:
        """Asigna categoría de contacto según bca_tipo.

        raise_if_not_found=False es OBLIGATORIO: el computed puede ejecutarse
        antes de que partner_categories.xml esté cargado en la instalación inicial,
        causando ValueError sin esta bandera.
        """
        xmlid_map = {
            'holding':     'BCA_Seguros.partner_cat_holding',
            'aseguradora': 'BCA_Seguros.partner_cat_aseguradora',
            'promotoria':  'BCA_Seguros.partner_cat_promotoria',
            'agente':      'BCA_Seguros.partner_cat_agente',
            'contratante': 'BCA_Seguros.partner_cat_contratante',
        }
        for rec in self:
            xmlid = xmlid_map.get(rec.bca_tipo)
            if xmlid:
                rec.bca_categoria_id = self.env.ref(xmlid, raise_if_not_found=False)
            else:
                rec.bca_categoria_id = False

    @api.constrains('bca_tipo', 'parent_id')
    def _check_jerarquia(self) -> None:
        """Valida que la jerarquía organizacional sea coherente:
        - Agente debe tener parent de tipo 'promotoria'
        - Promotoría debe tener parent de tipo 'holding'
        """
        for rec in self:
            if rec.bca_tipo == 'agente' and rec.parent_id:
                if rec.parent_id.bca_tipo != 'promotoria':
                    raise ValidationError(
                        f'Un agente debe pertenecer a una Promotoría BCA '
                        f'(parent actual: {rec.parent_id.bca_tipo or "sin tipo"}).'
                    )
            elif rec.bca_tipo == 'promotoria' and rec.parent_id:
                if rec.parent_id.bca_tipo != 'holding':
                    raise ValidationError(
                        f'Una Promotoría debe pertenecer a un Holding BCA '
                        f'(parent actual: {rec.parent_id.bca_tipo or "sin tipo"}).'
                    )
