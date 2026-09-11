"""Staging model for OCR-extracted carátula data.

``bca.ocr.documento`` is a transient-friendly staging record that:
1. Stores the uploaded PDF binary
2. Holds extracted text + parsed fields (editable by the user)
3. Creates the final ``bca.poliza`` in draft state

The model is *not* transient so the user can track extraction history,
but records older than 30 days should be purged by a scheduled action.
"""
from __future__ import annotations

import base64
import logging
from datetime import date, timedelta
from typing import Any

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..extractors.base import detectar_layout
from ..ocr_engines.pypdf_engine import PypdfEngine
from ..helpers import (
    find_or_create_partner,
    normalizar_moneda,
    resolver_agente,
    resolver_producto,
)

_logger = logging.getLogger(__name__)

ESTADO_SELECTION = [
    ('nuevo', 'Nuevo'),
    ('procesando', 'Procesando'),
    ('extraido', 'Extraído'),
    ('validado', 'Validado'),
    ('creado', 'Póliza Creada'),
    ('error', 'Error'),
]

_layout_engine = PypdfEngine()


class BcaOcrDocumento(models.Model):
    _name = 'bca.ocr.documento'
    _description = 'Documento OCR — Carátula de Póliza'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ── Archivo ────────────────────────────────────────────────────
    archivo_pdf: bytes = fields.Binary(
        string='Archivo PDF',
        required=True,
        attachment=True,
    )
    archivo_nombre: str = fields.Char(string='Nombre del Archivo')

    # ── Texto extraído ────────────────────────────────────────────
    texto_extraido: str = fields.Text(
        string='Texto Extraído',
        readonly=True,
    )
    layout_detectado: str = fields.Selection(
        [('gmm', 'GMM'), ('vida', 'Vida'), ('desconocido', 'Desconocido')],
        string='Layout Detectado',
        readonly=True,
    )

    # ── Estado ─────────────────────────────────────────────────────
    estado: str = fields.Selection(
        ESTADO_SELECTION,
        string='Estado',
        default='nuevo',
        tracking=True,
        readonly=True,
    )
    error_mensaje: str = fields.Text(string='Error', readonly=True)

    # ── Campos extraídos — comunes ────────────────────────────────
    poliza_numero: str = fields.Char(string='Nº de Póliza')
    contratante_nombre: str = fields.Char(string='Contratante')
    asegurado_nombre: str = fields.Char(string='Asegurado')
    producto_pdf: str = fields.Char(
        string='Producto (PDF)',
        help='Nombre del producto tal como aparece en la carátula.',
    )
    agente_clave: str = fields.Char(string='Clave Agente')
    periodicidad: str = fields.Selection(
        [('mensual', 'Mensual'), ('trimestral', 'Trimestral'),
         ('semestral', 'Semestral'), ('anual', 'Anual')],
        string='Periodicidad',
    )
    forma_pago_pdf: str = fields.Char(string='Forma de Pago (PDF)')

    # ── Fechas ─────────────────────────────────────────────────────
    fecha_emision: str = fields.Char(
        string='Fecha Emisión (ISO)',
        help='Fecha de emisión extraída del PDF en formato YYYY-MM-DD.',
    )
    fecha_inicio: str = fields.Char(
        string='Fecha Inicio (ISO)',
        help='Fecha de inicio de vigencia. Editar si la extracción falló.',
    )
    fecha_fin: str = fields.Char(
        string='Fecha Fin (ISO)',
        help='Fecha de fin de vigencia. Editar si la extracción falló.',
    )

    # ── Montos — Monetary ─────────────────────────────────────────
    currency_id: int = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
    )
    prima_monto: float = fields.Monetary(
        string='Prima Total / Anual',
        currency_field='currency_id',
    )

    # ── GMM-only ──────────────────────────────────────────────────
    prima_neta: float = fields.Monetary(
        string='Prima Neta', currency_field='currency_id',
    )
    iva: float = fields.Monetary(
        string='IVA', currency_field='currency_id',
    )
    recargo_frac: float = fields.Monetary(
        string='Recargo Fraccionamiento', currency_field='currency_id',
    )
    deducible: float = fields.Monetary(
        string='Deducible', currency_field='currency_id',
    )
    coaseguro: float = fields.Float(string='Coaseguro (%)')
    plan: str = fields.Char(string='Plan')
    nivel_hospitalario: str = fields.Char(string='Nivel Hospitalario')

    # ── Vida-only ─────────────────────────────────────────────────
    suma_asegurada: float = fields.Monetary(
        string='Suma Asegurada', currency_field='currency_id',
    )
    recargo_fijo: float = fields.Monetary(
        string='Recargo Fijo', currency_field='currency_id',
    )
    rfc: str = fields.Char(string='RFC')
    prima_forma_pago: float = fields.Monetary(
        string='Prima según Forma de Pago', currency_field='currency_id',
    )

    # ── Beneficiarios (texto crudo) ───────────────────────────────
    beneficiarios_texto: str = fields.Text(
        string='Beneficiarios (texto)',
        help='Texto crudo de la tabla de beneficiarios / asegurados.',
    )

    # ── Resultado ─────────────────────────────────────────────────
    poliza_id: int = fields.Many2one(
        'bca.poliza',
        string='Póliza Creada',
        readonly=True,
    )

    # ===================================================================
    # Actions
    # ===================================================================
    def action_extraer(self) -> bool:
        """Extract text from PDF and parse fields using layout-specific regex."""
        self.ensure_one()
        self.write({'estado': 'procesando', 'error_mensaje': False})

        if not self.archivo_pdf:
            raise UserError(_('No hay archivo PDF adjunto.'))

        # 1) Extract text
        pdf_bytes = base64.b64decode(self.archivo_pdf)
        texto = _layout_engine.extraer_texto(pdf_bytes)
        if not texto:
            self.write({
                'estado': 'error',
                'error_mensaje': _(
                    'No se pudo extraer texto del PDF. '
                    'Parece ser un PDF escaneado sin capa de texto.'
                ),
            })
            return False

        # 2) Detect layout
        layout = detectar_layout(texto)
        if layout == 'desconocido':
            self.write({
                'estado': 'error',
                'texto_extraido': texto,
                'layout_detectado': layout,
                'error_mensaje': _(
                    'No se reconoce el formato del documento. '
                    'Solo se soportan carátulas MetLife (GMM y Vida).'
                ),
            })
            return False

        # 3) Run extractor
        extractor = self._get_extractor(layout)
        try:
            data = extractor.extract(texto)
        except Exception as exc:
            _logger.exception('Extractor error for layout %s', layout)
            self.write({
                'estado': 'error',
                'texto_extraido': texto,
                'layout_detectado': layout,
                'error_mensaje': _('Error en extracción: %s') % exc,
            })
            return False

        # 4) Map data to staging fields
        vals = self._map_data_to_vals(data)
        vals['texto_extraido'] = texto
        vals['layout_detectado'] = layout
        vals['estado'] = 'extraido'
        self.write(vals)
        return True

    def action_crear_poliza(self) -> dict:
        """Create a bca.poliza in draft from the extracted staging data."""
        self.ensure_one()
        if self.estado not in ('extraido', 'validado'):
            raise UserError(_('Primero debe extraer los datos del PDF.'))
        if not self.poliza_numero:
            raise UserError(_('Falta el número de póliza.'))
        if self.poliza_id:
            raise UserError(_('Ya se creó la póliza %s.') % self.poliza_id.display_name)

        poliza = self._crear_poliza_from_staging()
        self.write({
            'estado': 'creado',
            'poliza_id': poliza.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Póliza %s') % poliza.name,
            'res_model': 'bca.poliza',
            'res_id': poliza.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_ver_texto(self) -> dict:
        """Open a dialog showing the raw extracted text."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Texto Extraído'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_ref': 'BCA_seguros_ocr.view_ocr_documento_texto_form'},
        }

    def action_abrir_poliza(self) -> dict:
        """Open the created poliza form."""
        self.ensure_one()
        if not self.poliza_id:
            raise UserError(_('No se ha creado la póliza aún.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Póliza %s') % self.poliza_id.display_name,
            'res_model': 'bca.poliza',
            'res_id': self.poliza_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ===================================================================
    # Extraction helpers
    # ===================================================================
    @staticmethod
    def _get_extractor(layout: str):
        """Return the appropriate extractor for the detected layout."""
        if layout == 'gmm':
            from ..extractors.metlife_gmm import MetlifeGmmExtractor
            return MetlifeGmmExtractor()
        if layout == 'vida':
            from ..extractors.metlife_vida import MetlifeVidaExtractor
            return MetlifeVidaExtractor()
        raise UserError(_('Layout no soportado: %s') % layout)

    def _map_data_to_vals(self, data: dict) -> dict:
        """Map extractor output dict to ORM write vals."""
        vals: dict[str, Any] = {}
        field_map = {
            'poliza_numero': 'poliza_numero',
            'contratante_nombre': 'contratante_nombre',
            'asegurado_nombre': 'asegurado_nombre',
            'producto_pdf': 'producto_pdf',
            'agente_clave': 'agente_clave',
            'periodicidad': 'periodicidad',
            'forma_pago_pdf': 'forma_pago_pdf',
            'plan': 'plan',
            'nivel_hospitalario': 'nivel_hospitalario',
            'rfc': 'rfc',
        }
        for src, dst in field_map.items():
            if data.get(src) is not None:
                vals[dst] = data[src]

        # Monetary fields
        monetary = [
            'prima_monto', 'prima_neta', 'iva', 'recargo_frac', 'deducible',
            'suma_asegurada', 'recargo_fijo', 'prima_forma_pago',
        ]
        source_map = {'prima_monto': 'prima_total'}
        for field_name in monetary:
            source = source_map.get(field_name, field_name)
            val = data.get(source)
            if val is not None:
                vals[field_name] = float(val)

        # Float
        coaseguro = data.get('coaseguro')
        if coaseguro is not None:
            vals['coaseguro'] = float(coaseguro)

        # Dates
        for date_field in ('fecha_emision', 'fecha_inicio', 'fecha_fin'):
            val = data.get(date_field)
            if val:
                vals[date_field] = val

        # Beneficiarios as text
        beneficiarios = data.get('beneficiarios', [])
        if beneficiarios:
            lineas = []
            for b in beneficiarios:
                lineas.append(
                    '%s|%s|%.0f%%' % (b['nombre'], b['parentesco'], b['porcentaje'])
                )
            vals['beneficiarios_texto'] = '\n'.join(lineas)

        return vals

    # ===================================================================
    # Póliza creation
    # ===================================================================
    def _crear_poliza_from_staging(self):
        """Resolve references and create bca.poliza in draft."""
        self.ensure_one()
        env = self.env

        # 1) Aseguradora — MetLife
        aseguradora = env['res.partner'].search([
            ('bca_tipo', '=', 'aseguradora'),
            ('name', 'ilike', 'metlife'),
        ], limit=1)
        if not aseguradora:
            raise UserError(_(
                'No se encontró la aseguradora MetLife en la base de datos. '
                'Debe existir un contacto con tipo "Aseguradora" y nombre '
                'conteniendo "MetLife".'
            ))

        # 2) Ramo from layout
        ramo = 'gmm' if self.layout_detectado == 'gmm' else 'vida'

        # 3) Agente
        agente, agente_warn = resolver_agente(env, self.agente_clave, aseguradora.id)
        if agente_warn:
            _logger.warning('Agente warning: %s', agente_warn)
            # Don't abort — leave agente_id empty for user to fix

        # 4) Producto
        producto, prod_warn = resolver_producto(
            env, self.producto_pdf, ramo, aseguradora.id,
        )
        if prod_warn:
            _logger.warning('Producto warning: %s', prod_warn)

        if not producto:
            raise UserError(_(
                'No se encontró el producto "%s" (ramo %s) en el catálogo.\n\n'
                'Verifique que:\n'
                '• El producto esté registrado en Odoo\n'
                '• La aseguradora sea MetLife\n'
                '• El ramo coincida (%s)\n\n'
                'Si el nombre en el PDF difiere del catálogo, '
                'actualice el campo "Nombre archivo aseguradora" en el producto.'
            ) % (self.producto_pdf or '(vacío)', ramo, ramo))

        # 5) Moneda
        moneda = env.ref('base.MXN', raise_if_not_found=False)
        if not moneda:
            moneda = env.company.currency_id

        # 6) Contratante
        contratante = find_or_create_partner(env, {
            'name': self.contratante_nombre or 'SIN NOMBRE',
        })

        # 7) Asegurado
        asegurado = False
        if self.asegurado_nombre and self.asegurado_nombre != self.contratante_nombre:
            asegurado = find_or_create_partner(env, {
                'name': self.asegurado_nombre,
            })

        # 8) Fechas
        fecha_emision = self._parse_iso_date(self.fecha_emision)
        fecha_inicio = self._parse_iso_date(self.fecha_inicio) or fecha_emision
        fecha_fin = self._parse_iso_date(self.fecha_fin)

        # Auto-calculate fecha_fin if missing: +1 year from inicio
        if fecha_inicio and not fecha_fin:
            from dateutil.relativedelta import relativedelta
            fecha_fin = fecha_inicio + relativedelta(years=1)

        # Fallback: if no dates at all, use today + 1 year
        if not fecha_inicio:
            from odoo import fields as odoo_fields
            today = odoo_fields.Date.context_today(self)
            fecha_inicio = today
            fecha_fin = today + timedelta(days=365)

        # 9) Build vals
        vals: dict[str, Any] = {
            'name': self.poliza_numero,
            'aseguradora_id': aseguradora.id,
            'ramo': ramo,
            'periodicidad': self.periodicidad or 'anual',
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'currency_id': moneda.id,
            'prima_anual': self.prima_monto or 0.0,
            'contratante_id': contratante.id,
            'estado': 'borrador',
        }

        # Optional references
        if agente:
            vals['agente_id'] = agente.id
        if producto:
            vals['producto_id'] = producto.id
        if asegurado:
            vals['asegurado_id'] = asegurado.id
        if fecha_emision:
            vals['fecha_emision'] = fecha_emision

        # GMM fields
        if ramo == 'gmm':
            vals.update({
                'deducible': self.deducible,
                'coaseguro': self.coaseguro,
                'iva': self.iva,
                'recargo_fraccionamiento': self.recargo_frac,
                'plan': self.plan,
                'nivel_hospitalario': self.nivel_hospitalario,
            })
        else:
            vals.update({
                'suma_asegurada': self.suma_asegurada,
                'recargo_fijo': self.recargo_fijo,
                'prima_fraccionada': self.prima_forma_pago,
            })

        poliza = env['bca.poliza'].create(vals)

        # 10) Beneficiarios (Vida)
        if ramo == 'vida' and self.beneficiarios_texto:
            self._crear_beneficiarios(poliza)

        return poliza

    def _crear_beneficiarios(self, poliza) -> None:
        """Parse beneficiarios_texto and create bca.poliza.beneficiario lines."""
        self.ensure_one()
        for linea in (self.beneficiarios_texto or '').strip().split('\n'):
            partes = linea.split('|')
            if len(partes) < 3:
                continue
            nombre = partes[0].strip()
            parentesco = partes[1].strip()
            pct_str = partes[2].strip().replace('%', '').strip()
            try:
                porcentaje = float(pct_str)
            except ValueError:
                continue
            if not nombre:
                continue
            partner = find_or_create_partner(self.env, {'name': nombre})
            self.env['bca.poliza.beneficiario'].create({
                'poliza_id': poliza.id,
                'beneficiario_id': partner.id,
                'parentesco': parentesco,
                'porcentaje': porcentaje,
            })

    @staticmethod
    def _parse_iso_date(valor: str | None) -> date | None:
        """Parse YYYY-MM-DD string to date, or return None."""
        if not valor:
            return None
        try:
            return date.fromisoformat(valor.strip())
        except (ValueError, TypeError):
            return None
