from __future__ import annotations

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

ESTADO_RECIBO_SELECTION = [
    ('pendiente', 'Pendiente'),
    ('pagado', 'Pagado'),
    ('cancelado', 'Cancelado'),
]

CAMPOS_PCA_PROTEGIDOS = {'pca_aplicada', 'factor_aplicado'}


class BcaRecibo(models.Model):
    _name = 'bca.recibo'
    _description = 'Recibo de Póliza BCA'
    _inherit = ['mail.thread']
    _order = 'poliza_id, numero_recibo'

    name: str = fields.Char(
        string='Folio',
        default=lambda self: self.env['ir.sequence'].next_by_code('bca.recibo'),
        readonly=True,
        copy=False,
    )
    poliza_id: int = fields.Many2one(
        'bca.poliza',
        string='Póliza',
        required=True,
        ondelete='restrict',
        index=True,
    )
    # Foto inmutable del agente/promotoría al momento del pago.
    # Asignado por action_registrar_pago — NO confiar en poliza.agente_id
    # para reportes históricos (puede cambiar vía cambiar_agente()).
    agente_id: int = fields.Many2one(
        'res.partner',
        string='Agente (al pagar)',
        ondelete='restrict',
        domain=[('bca_tipo', '=', 'agente')],
    )
    promotoria_id: int = fields.Many2one(
        'res.partner',
        string='Promotoría (al pagar)',
        ondelete='restrict',
    )
    numero_recibo: int = fields.Integer(
        string='Número de Recibo',
        readonly=True,
        help='Secuencia dentro de la póliza (1, 2, 3...).',
    )
    fecha_desde: fields.Date = fields.Date(string='Cobertura Desde', required=True)
    fecha_hasta: fields.Date = fields.Date(string='Cobertura Hasta', required=True)

    monto_modal: float = fields.Monetary(
        string='Prima Modal',
        currency_field='currency_id',
    )
    recargo: float = fields.Monetary(
        string='Recargo',
        currency_field='currency_id',
    )
    prima_neta: float = fields.Monetary(
        string='Prima Neta',
        currency_field='currency_id',
        help='Base para el cálculo de PCA.',
    )
    prima_total: float = fields.Monetary(
        string='Prima Total',
        currency_field='currency_id',
        help='Lo que paga el cliente (incluye recargo e impuestos).',
    )
    currency_id: int = fields.Many2one(
        'res.currency',
        related='poliza_id.currency_id',
        store=True,
        readonly=True,
    )

    estado: str = fields.Selection(
        ESTADO_RECIBO_SELECTION,
        string='Estado',
        default='pendiente',
        required=True,
        tracking=True,
        index=True,
    )
    fecha_pago: fields.Date = fields.Date(string='Fecha de Pago')
    conducto_id: int = fields.Many2one(
        'bca.conducto',
        string='Conducto',
        ondelete='restrict',
    )
    folio_endoso: str = fields.Char(
        string='Folio de Endoso',
        help='Solo aplica para ramo GMM.',
    )

    # PCA congelada al pago. Inmutable salvo por env.su o cancelación autorizada.
    pca_aplicada: float = fields.Monetary(
        string='PCA Aplicada',
        currency_field='currency_id',
        readonly=True,
        tracking=True,
    )
    factor_aplicado: float = fields.Float(
        string='Factor Aplicado',
        digits=(6, 4),
        readonly=True,
        tracking=True,
    )
    motivo_exclusion_pca: str = fields.Char(
        string='Motivo Exclusión PCA',
        help='Razón por la que la PCA es 0 (ej: aportación adicional).',
    )
    bitacora_linea_id: int = fields.Many2one(
        'bca.bitacora.linea',
        string='Línea de Bitácora',
        ondelete='set null',
        help='Línea de la importación de cobranza que generó este pago.',
    )

    # Unicidad del número de recibo dentro de una póliza.
    _unique_numero_por_poliza = models.Constraint(
        'UNIQUE(poliza_id, numero_recibo)',
        'El número de recibo debe ser único dentro de cada póliza.',
    )

    @api.constrains('fecha_desde', 'fecha_hasta')
    def _check_fechas(self) -> None:
        for rec in self:
            if rec.fecha_desde and rec.fecha_hasta and rec.fecha_desde >= rec.fecha_hasta:
                raise ValidationError(
                    _('Fecha desde debe ser anterior a fecha hasta.')
                )

    def write(self, vals: dict) -> bool:
        """C1: bloquea edición de PCA en recibos pagados.

        Escape autorizado:
        - self.env.su (superusuario / acciones internas del módulo)
        - bypass explícito vía contexto allow_pca_edit=True (usado por
          action_cancelar_pago tras chequeo de grupo).
        """
        if (set(vals) & CAMPOS_PCA_PROTEGIDOS
                and not self.env.su
                and not self.env.context.get('allow_pca_edit')):
            for rec in self:
                if rec.estado == 'pagado':
                    raise UserError(
                        _('PCA y factor de recibo pagado son inmutables '
                          '(recibo %s).') % rec.name
                    )
        return super().write(vals)

    def action_registrar_pago(self, vals: dict) -> bool:
        """R-COB-09: valida precondiciones ANTES de tocar BD.

        Si fecha_pago o prima_neta no vienen, levantamos sin haber
        modificado nada — la BD queda intacta y el recibo sigue pendiente.
        """
        if not vals.get('fecha_pago'):
            raise ValidationError(_('La fecha de pago es obligatoria.'))
        if not vals.get('prima_neta') or vals['prima_neta'] <= 0:
            raise ValidationError(_('La prima neta debe ser un valor positivo.'))

        for rec in self:
            if rec.estado != 'pendiente':
                raise UserError(
                    _("Solo se pueden pagar recibos en estado 'Pendiente' "
                      "(recibo %s, estado %s).") % (rec.name, rec.estado)
                )

            # FIFO: este recibo debe ser el más antiguo pendiente de la póliza.
            pendientes = rec.poliza_id.recibo_ids.filtered(
                lambda r: r.estado == 'pendiente'
            )
            fifo = pendientes.sorted('numero_recibo')[:1]
            if fifo and fifo.id != rec.id:
                raise UserError(
                    _('Debe pagarse el recibo %s antes que el %s (FIFO).')
                    % (fifo.name, rec.name)
                )

            pca, factor, motivo = rec._calcular_pca()
            # Usa super().write para esquivar nuestro propio bloqueo de write()
            # (el recibo aún no está 'pagado' cuando entra aquí, pero el
            # contexto allow_pca_edit deja explícita la autoría del cambio).
            super(BcaRecibo, rec.with_context(allow_pca_edit=True)).write({
                'estado': 'pagado',
                'fecha_pago': vals['fecha_pago'],
                'prima_neta': vals['prima_neta'],
                'prima_total': vals.get('prima_total', vals['prima_neta']),
                'recargo': vals.get('recargo', 0.0),
                'conducto_id': vals.get('conducto_id'),
                'folio_endoso': vals.get('folio_endoso'),
                'agente_id': rec.poliza_id.agente_id.id,
                'promotoria_id': rec.poliza_id.promotoria_id.id,
                'pca_aplicada': pca,
                'factor_aplicado': factor,
                'motivo_exclusion_pca': motivo,
                'bitacora_linea_id': vals.get('bitacora_linea_id'),
            })
        return True

    def action_registrar_pago_ui(self) -> bool:
        """Wrapper UI: toma los valores ya editados en el form y registra el pago.

        Diseñado para el botón "Registrar Pago" del form view. El usuario debe
        haber completado fecha_pago, prima_neta y conducto_id antes de presionar.
        """
        self.ensure_one()
        return self.action_registrar_pago({
            'fecha_pago': self.fecha_pago,
            'prima_neta': self.prima_neta,
            'prima_total': self.prima_total or self.prima_neta,
            'recargo': self.recargo,
            'conducto_id': self.conducto_id.id if self.conducto_id else False,
            'folio_endoso': self.folio_endoso,
        })

    def action_cancelar_pago(self) -> bool:
        """M5: cancela un pago. Solo Director General o Director Comercial.

        Validación explícita de grupo además de la ACL — la ACL restringe
        write/unlink pero no impide ejecutar el método por sí sola.
        """
        if not (self.env.user.has_group('BCA_Seguros.group_bca_director')
                or self.env.user.has_group('BCA_Seguros.group_bca_director_comercial')):
            raise AccessError(
                _('Solo Director General o Director Comercial pueden cancelar pagos.')
            )
        for rec in self:
            if rec.estado != 'pagado':
                raise UserError(
                    _("Solo se pueden cancelar recibos en estado 'Pagado' "
                      "(recibo %s, estado %s).") % (rec.name, rec.estado)
                )
            rec.with_context(allow_pca_edit=True).write({
                'estado': 'cancelado',
                'pca_aplicada': 0.0,
                'factor_aplicado': 0.0,
            })
        return True

    def _calcular_pca(self) -> tuple:
        """Delega al calculador registrado para la aseguradora.

        Mientras los calculadores reales no estén implementados (Etapa 7),
        atrapamos NotImplementedError para no bloquear el flujo de pago
        durante el desarrollo de E2-E6. El registry levantará KeyError
        si la aseguradora no tiene calculador asignado.
        """
        from ..calculadores_pca import CALCULADOR_REGISTRY
        self.ensure_one()
        codigo = self.poliza_id.aseguradora_id.bca_codigo_aseguradora
        if not codigo:
            raise UserError(
                _('La aseguradora %s no tiene código asignado.')
                % self.poliza_id.aseguradora_id.display_name
            )
        if codigo not in CALCULADOR_REGISTRY:
            raise UserError(
                _('No hay calculador de PCA registrado para %s.') % codigo
            )
        try:
            return CALCULADOR_REGISTRY[codigo](self.env).calcular(self)
        except NotImplementedError:
            # Stub temporal hasta Etapa 7 — permite ejercitar el flujo E2.
            return (0.0, 0.0, 'Calculador pendiente — Etapa 7')
