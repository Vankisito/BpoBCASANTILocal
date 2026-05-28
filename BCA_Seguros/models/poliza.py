from __future__ import annotations

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .product_template import RAMO_SELECTION

PERIODICIDAD_SELECTION = [
    ('mensual', 'Mensual'),
    ('trimestral', 'Trimestral'),
    ('semestral', 'Semestral'),
    ('anual', 'Anual'),
]
ESTADO_SELECTION = [
    ('borrador', 'Borrador'),
    ('activa', 'Activa'),
    ('vencida', 'Vencida'),
    ('cancelada', 'Cancelada'),
]
TIPO_COBERTURA_SELECTION = [
    ('estandar', 'Estándar'),
    ('accidentes', 'Accidentes'),
    ('invalidez', 'Invalidez'),
]

# meses por período — usado en _generar_plan_pagos
MESES_POR_PERIODO = {
    'mensual': 1,
    'trimestral': 3,
    'semestral': 6,
    'anual': 12,
}


class BcaPoliza(models.Model):
    _name = 'bca.poliza'
    _description = 'Póliza BCA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_inicio desc, name desc'

    name: str = fields.Char(
        string='Número de Póliza',
        required=True,
        index=True,
        tracking=True,
    )
    aseguradora_id: int = fields.Many2one(
        'res.partner',
        string='Aseguradora',
        required=True,
        ondelete='restrict',
        domain=[('bca_tipo', '=', 'aseguradora')],
        index=True,
    )
    producto_id: int = fields.Many2one(
        'product.template',
        string='Producto',
        required=True,
        ondelete='restrict',
        domain=[('bca_es_producto_seguro', '=', True)],
    )
    # Computed-editable: se autocompleta desde el producto (compat. con
    # imports/tests que crean la póliza con producto_id y sin ramo), pero es
    # editable para usarlo como filtro intermedio de la cascada
    # Aseguradora → Ramo → Productos en la vista.
    ramo: str = fields.Selection(
        RAMO_SELECTION,
        string='Ramo',
        compute='_compute_ramo',
        store=True,
        readonly=False,
    )
    agente_id: int = fields.Many2one(
        'res.partner',
        string='Agente',
        required=True,
        ondelete='restrict',
        domain=[('bca_tipo', '=', 'agente')],
        tracking=True,
        index=True,
    )
    # C2: computed SIN store — siempre refleja parent_id actual del agente.
    # search= permite filtrar/agrupar desde la UI y la API.
    promotoria_id: int = fields.Many2one(
        'res.partner',
        string='Promotoría',
        compute='_compute_promotoria_id',
        store=False,
        search='_search_promotoria_id',
    )
    contratante_id: int = fields.Many2one(
        'res.partner',
        string='Contratante',
        required=True,
        ondelete='restrict',
        domain=[('bca_tipo', '=', 'contratante')],
    )
    poliza_origen_id: int = fields.Many2one(
        'bca.poliza',
        string='Póliza Origen',
        ondelete='set null',
        help='Si esta póliza es renovación o conversión, apunta a la póliza anterior.',
    )
    currency_id: int = fields.Many2one(
        'res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    prima_anual: float = fields.Monetary(
        string='Prima Anual',
        currency_field='currency_id',
    )
    prima_fraccionada: float = fields.Monetary(
        string='Prima Fraccionada',
        currency_field='currency_id',
        help='Prima por recibo (prima_anual dividida entre el número de períodos).',
    )
    recargo_fraccionamiento: float = fields.Monetary(
        string='Recargo Fraccionamiento',
        currency_field='currency_id',
    )
    suma_asegurada: float = fields.Monetary(
        string='Suma Asegurada',
        currency_field='currency_id',
    )

    periodicidad: str = fields.Selection(
        PERIODICIDAD_SELECTION,
        string='Periodicidad',
        required=True,
        default='anual',
    )
    fecha_inicio: fields.Date = fields.Date(string='Fecha de Inicio', required=True)
    fecha_fin: fields.Date = fields.Date(string='Fecha de Fin', required=True)

    # C1: computed almacenado. Único punto de actualización de pagado_hasta.
    # El ORM lo recalcula automáticamente al cambiar estado/fecha_hasta de recibos.
    pagado_hasta: fields.Date = fields.Date(
        string='Pagado Hasta',
        compute='_compute_pagado_hasta',
        store=True,
        readonly=True,
        tracking=True,
    )
    estado: str = fields.Selection(
        ESTADO_SELECTION,
        string='Estado',
        default='borrador',
        required=True,
        tracking=True,
        index=True,
    )

    # Campos GMM
    deducible: float = fields.Monetary(
        string='Deducible',
        currency_field='currency_id',
        help='Solo aplica para ramo GMM.',
    )
    coaseguro: float = fields.Float(
        string='Coaseguro (%)',
        help='Solo aplica para ramo GMM. Porcentaje en formato 0.05 = 5%.',
    )
    nivel_hospitalario: str = fields.Char(
        string='Nivel Hospitalario',
        help='Solo aplica para ramo GMM.',
    )

    # Campos Vida
    tipo_cobertura: str = fields.Selection(
        TIPO_COBERTURA_SELECTION,
        string='Tipo de Cobertura',
        help='Solo aplica para ramo Vida.',
    )
    temporalidad_anios: int = fields.Integer(
        string='Temporalidad (años)',
        help='Solo aplica para ramo Vida. Años de vigencia.',
    )
    es_aportacion_adicional: bool = fields.Boolean(
        string='Aportación Adicional',
        help='Solo aplica para Vida capitalizable. Excluye recibo de PCA.',
    )

    recibo_ids: list[int] = fields.One2many(
        'bca.recibo',
        'poliza_id',
        string='Recibos',
    )
    cambio_agente_ids: list[int] = fields.One2many(
        'bca.poliza.cambio.agente',
        'poliza_id',
        string='Historial de Cambios de Agente',
    )

    recibo_count: int = fields.Integer(
        string='# Recibos',
        compute='_compute_recibo_count',
    )
    cambio_agente_count: int = fields.Integer(
        string='# Cambios de Agente',
        compute='_compute_cambio_agente_count',
    )

    # R-POL-01: número de póliza único por aseguradora.
    _unique_name_aseguradora = models.Constraint(
        'UNIQUE(name, aseguradora_id)',
        'El número de póliza debe ser único por aseguradora.',
    )

    @api.depends('producto_id')
    def _compute_ramo(self) -> None:
        for pol in self:
            if pol.producto_id:
                pol.ramo = pol.producto_id.bca_ramo

    @api.onchange('aseguradora_id', 'ramo')
    def _onchange_filtros_producto(self) -> None:
        """Cascada Aseguradora → Ramo → Productos: si el producto elegido ya
        no cumple los filtros de aseguradora/ramo, lo limpia."""
        for pol in self:
            prod = pol.producto_id
            if not prod:
                continue
            if (pol.aseguradora_id and prod.bca_aseguradora_id != pol.aseguradora_id) \
                    or (pol.ramo and prod.bca_ramo != pol.ramo):
                pol.producto_id = False

    @api.onchange('fecha_inicio', 'periodicidad', 'temporalidad_anios', 'ramo')
    def _onchange_fecha_fin(self) -> None:
        """Sugiere fecha_fin (editable): Vida = inicio + temporalidad_anios;
        otros ramos = inicio + 1 año. No se ejecuta en create (los imports de
        portafolio fijan su propio fecha_fin)."""
        for pol in self:
            if not pol.fecha_inicio:
                continue
            if pol.ramo == 'vida' and pol.temporalidad_anios:
                pol.fecha_fin = pol.fecha_inicio + relativedelta(years=pol.temporalidad_anios)
            else:
                pol.fecha_fin = pol.fecha_inicio + relativedelta(years=1)

    @api.depends('agente_id', 'agente_id.parent_id')
    def _compute_promotoria_id(self) -> None:
        for pol in self:
            pol.promotoria_id = pol.agente_id.parent_id if pol.agente_id else False

    def _search_promotoria_id(self, operator: str, value: object) -> list:
        return [('agente_id.parent_id', operator, value)]

    @api.depends('recibo_ids')
    def _compute_recibo_count(self) -> None:
        for pol in self:
            pol.recibo_count = len(pol.recibo_ids)

    @api.depends('cambio_agente_ids')
    def _compute_cambio_agente_count(self) -> None:
        for pol in self:
            pol.cambio_agente_count = len(pol.cambio_agente_ids)

    @api.depends('recibo_ids.estado', 'recibo_ids.fecha_hasta')
    def _compute_pagado_hasta(self) -> None:
        """C1: Recalcula pagado_hasta como máxima fecha_hasta de recibos pagados.

        El ORM dispara este compute automáticamente cuando un recibo cambia
        estado o fecha_hasta — tanto al pagar (avanza) como al cancelar pago
        (retrocede). No existe ningún otro punto de actualización del campo.
        """
        for pol in self:
            ultimo = pol.recibo_ids.filtered(
                lambda r: r.estado == 'pagado'
            ).sorted('fecha_hasta', reverse=True)[:1]
            pol.pagado_hasta = ultimo.fecha_hasta if ultimo else False

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self) -> None:
        for pol in self:
            if pol.fecha_inicio and pol.fecha_fin and pol.fecha_inicio >= pol.fecha_fin:
                raise ValidationError(
                    _('La fecha de inicio debe ser anterior a la fecha de fin.')
                )

    def action_confirmar(self) -> bool:
        """Borrador → Activa. Genera el plan de pagos."""
        for pol in self:
            if pol.estado != 'borrador':
                raise ValidationError(
                    _("Solo pólizas en estado 'Borrador' pueden confirmarse "
                      "(actual: %s).") % pol.estado
                )
            pol.estado = 'activa'
            pol._generar_plan_pagos()
        return True

    def action_cancelar(self) -> bool:
        """Pasa la póliza a estado cancelada. No borra recibos (auditoría)."""
        for pol in self:
            pol.estado = 'cancelada'
        return True

    def _crear_recibos_anualidad(self, inicio, numero_inicial: int):
        """Crea los recibos de UN año-póliza (anualidad) a partir de `inicio`.

        El número de recibos por anualidad depende solo de la periodicidad
        (mensual→12, trimestral→4, semestral→2, anual→1). La prima_anual se
        fracciona dentro de cada año. El último recibo se topa a fecha_fin.
        """
        self.ensure_one()
        meses = MESES_POR_PERIODO[self.periodicidad]
        recibos_por_anio = 12 // meses
        prima_por_recibo = (
            (self.prima_anual or 0.0) / recibos_por_anio if recibos_por_anio else 0.0
        )
        fin_anualidad = inicio + relativedelta(years=1)
        if fin_anualidad > self.fecha_fin:
            fin_anualidad = self.fecha_fin

        # bca_generando_plan: evita que el create() de bca.recibo redirija al
        # recibo pendiente (esa protección es solo para la creación manual).
        Recibo = self.env['bca.recibo'].with_context(bca_generando_plan=True)
        creados = self.env['bca.recibo']
        numero = numero_inicial
        for i in range(recibos_por_anio):
            fecha_desde = inicio + relativedelta(months=meses * i)
            if fecha_desde >= fin_anualidad:
                break
            fecha_hasta = inicio + relativedelta(months=meses * (i + 1))
            if fecha_hasta > fin_anualidad:
                fecha_hasta = fin_anualidad
            creados |= Recibo.create({
                'poliza_id': self.id,
                'numero_recibo': numero,
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'prima_neta': prima_por_recibo,
                'monto_modal': prima_por_recibo,
            })
            numero += 1
        return creados

    def _generar_plan_pagos(self) -> list[int]:
        """Genera los recibos del PRIMER año-póliza (anualidad vigente).

        El resto del término se materializa anualidad por anualidad vía
        _generar_siguiente_anualidad (avance automático al pagar o botón
        manual), para no crear cientos de recibos de golpe en pólizas largas.

        R-POL-05: No se ejecuta si ya hay recibos pagados — protege contra
        regeneración accidental que destruiría el historial de pagos.
        """
        self.ensure_one()
        if self.recibo_ids.filtered(lambda r: r.estado == 'pagado'):
            raise UserError(
                _('No se puede regenerar el plan de pagos: ya hay recibos pagados.')
            )

        # Si había recibos solo pendientes (de un intento previo), descartarlos.
        self.recibo_ids.filtered(lambda r: r.estado == 'pendiente').unlink()
        return self._crear_recibos_anualidad(self.fecha_inicio, 1).ids

    def _generar_siguiente_anualidad(self) -> list[int]:
        """Genera la siguiente anualidad si aún queda término por cubrir.

        Toma el fin de la última anualidad generada (máx fecha_hasta de los
        recibos existentes) y crea el año siguiente, numerando a continuación.
        Idempotente respecto al término: no genera nada si ya se llegó a
        fecha_fin.
        """
        self.ensure_one()
        if not self.recibo_ids:
            return []
        ultimo_fin = max(self.recibo_ids.mapped('fecha_hasta'))
        if ultimo_fin >= self.fecha_fin:
            return []
        numero_inicial = max(self.recibo_ids.mapped('numero_recibo')) + 1
        return self._crear_recibos_anualidad(ultimo_fin, numero_inicial).ids

    def action_generar_siguiente_anualidad(self) -> bool:
        """Botón manual: genera la siguiente anualidad (fallback al avance
        automático que ocurre al pagar el último recibo de la anualidad)."""
        self.ensure_one()
        if self.estado != 'activa':
            raise UserError(
                _('Solo pólizas activas pueden generar anualidades.')
            )
        if self.recibo_ids.filtered(lambda r: r.estado == 'pendiente'):
            raise UserError(
                _('Aún hay recibos pendientes en la anualidad actual.')
            )
        if not self._generar_siguiente_anualidad():
            raise UserError(
                _('No queda término por generar: la póliza ya cubre hasta su fecha de fin.')
            )
        return True

    def cambiar_agente(self, nuevo_agente, motivo: str) -> bool:
        """M4: Único punto autorizado para cambiar el agente de una póliza.

        Crea un registro en bca.poliza.cambio.agente con el snapshot
        organizacional antes y después del cambio. promotoria_id se recalcula
        sola (computed sin store).
        """
        self.ensure_one()
        if nuevo_agente.bca_tipo != 'agente':
            raise ValidationError(
                _('El nuevo titular debe ser de tipo Agente (recibido: %s).')
                % (nuevo_agente.bca_tipo or 'sin tipo')
            )
        self.env['bca.poliza.cambio.agente'].create({
            'poliza_id': self.id,
            'agente_anterior_id': self.agente_id.id,
            'promotoria_anterior_id': self.promotoria_id.id,
            'agente_nuevo_id': nuevo_agente.id,
            'promotoria_nueva_id': nuevo_agente.parent_id.id,
            'fecha_cambio': fields.Date.context_today(self),
            'motivo': motivo,
            'usuario_id': self.env.user.id,
        })
        self.agente_id = nuevo_agente
        return True

    def action_view_recibos(self) -> dict:
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Recibos de %s') % self.name,
            'res_model': 'bca.recibo',
            'view_mode': 'list,form',
            'domain': [('poliza_id', '=', self.id)],
            'context': {'default_poliza_id': self.id},
        }

    def action_view_cambios_agente(self) -> dict:
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Historial de Agentes — %s') % self.name,
            'res_model': 'bca.poliza.cambio.agente',
            'view_mode': 'list,form',
            'domain': [('poliza_id', '=', self.id)],
            'context': {'default_poliza_id': self.id},
        }
