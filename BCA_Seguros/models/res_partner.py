from __future__ import annotations

import re
import unicodedata

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import OrderedSet

# Eje "posición en la RED de distribución de BCA" (excluyente por contacto). El
# cliente de BCA es la ASEGURADORA (a quien BCA cobra comisiones); contratante y
# asegurado NO viven aquí: son roles de póliza (no excluyentes) expresados en los
# flags computados bca_es_contratante / bca_es_asegurado.
TIPO_SELECTION = [
    ('holding', 'Holding'),
    ('aseguradora', 'Aseguradora'),
    ('promotoria', 'Promotoría'),
    ('agente', 'Agente'),
]
# Entidades estructurales de la red que NUNCA pueden ser contratante/asegurado de
# una póliza; se excluyen de la deduplicación de personas y del domain de póliza.
TIPOS_RED_EXCLUIDOS_POLIZA = ('aseguradora', 'promotoria', 'holding')
# Nomenclatura de carrera del agente (BDD §"Agentes — identidad y nomenclatura").
# Es el estado POR ASEGURADORA y vive en el modelo puente
# res.partner.agente.aseguradora. En res.partner, bca_estado_agente es un
# rollup computado de estos valores (ver _compute_bca_estado_agente).
# Solo 'clave_definitiva' computa para PCA.
ESTADO_AGENTE_SELECTION = [
    ('prospecto', 'Prospecto'),
    ('clave_arranque', 'Clave de Arranque'),
    ('clave_definitiva', 'Clave Definitiva'),
]
# Prioridad para el rollup: el "mejor" estado alcanzado en alguna aseguradora.
_ESTADO_AGENTE_PRIORIDAD = ['clave_definitiva', 'clave_arranque', 'prospecto']
ESTADO_CIVIL_SELECTION = [
    ('soltero', 'Soltero(a)'),
    ('casado', 'Casado(a)'),
    ('divorciado', 'Divorciado(a)'),
    ('viudo', 'Viudo(a)'),
    ('union_libre', 'Unión Libre'),
]
GENERO_SELECTION = [
    ('masculino', 'Masculino'),
    ('femenino', 'Femenino'),
    ('otro', 'Otro'),
]
# Entes de la red BCA fiscalmente INDEPENDIENTES: cada uno (sea persona física o
# moral) tiene su propio RFC (`vat`) y domicilio fiscal y NO debe heredarlos de su
# ancestro en la jerarquía (holding/promotoría). Odoo, nativamente, sincroniza los
# "commercial fields" (vat) desde el commercial_partner_id y los "address fields"
# desde el padre `type='contact'`; para estos tipos se corta esa sincronización.
# El scoping es por bca_tipo (NO por is_company): una promotoría/agente persona
# física (is_company=False) colgaría fiscalmente del ancestro si nos apoyáramos en
# is_company, así que ese criterio no sirve como palanca. Ver _fields_sync,
# _commercial_sync_to_descendants y _update_address más abajo.
TIPOS_FISCAL_INDEPENDIENTE = ('promotoria', 'agente')
# Entes de la red que muestran SOLO su nombre en pantalla, sin el de la empresa
# a la que pertenecen. Petición del cliente (v19.0.1.11.0): Odoo nativo muestra
# "Contacto, Empresa" y estorba en listas y reportes. La relación parent_id
# (base de comisiones y reportes) NO se toca: solo cambia la representación,
# vía la key nativa `partner_display_name_hide_company` de _get_complete_name.
TIPOS_RED_NOMBRE_CORTO = ('agente', 'promotoria')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    bca_tipo: str = fields.Selection(
        TIPO_SELECTION,
        string='Tipo BCA',
        index=True,
    )
    # Rollup computado y almacenado del estado de carrera del agente: el "mejor"
    # estado alcanzado en cualquiera de sus aseguradoras (Definitiva > Arranque >
    # Prospecto; sin claves = Prospecto). NO se edita a mano: la fuente de verdad
    # es el modelo puente, que Reclutamiento alimenta vía automated actions.
    # Sirve solo para filtros/listas/visual; la PCA filtra por el estado del
    # PUENTE (clave_definitiva) por aseguradora, no por este campo.
    bca_estado_agente: str = fields.Selection(
        ESTADO_AGENTE_SELECTION,
        string='Estado Agente',
        compute='_compute_bca_estado_agente',
        store=True,
        index=True,
    )
    bca_codigo_aseguradora: str = fields.Char(
        string='Código Aseguradora',
        index=True,
    )

    # Datos demográficos del contratante (los faltantes en res.partner estándar).
    # RFC → campo estándar `vat`; domicilio → street/street2/city/zip/state_id.
    bca_fecha_nacimiento: fields.Date = fields.Date(string='Fecha de Nacimiento')
    bca_estado_civil: str = fields.Selection(
        ESTADO_CIVIL_SELECTION,
        string='Estado Civil',
    )
    bca_genero: str = fields.Selection(
        GENERO_SELECTION,
        string='Género',
    )
    # CURP: parte del Id interno PCA del agente (Nombre + RFC(`vat`) + CURP,
    # norma PCA Car. 2). RFC reusa el campo nativo `vat`. index para la búsqueda
    # de idempotencia de la conversión (Etapa 12 Fase C, D-15).
    bca_curp: str = fields.Char(
        string='CURP',
        index=True,
        copy=False,
    )

    agente_aseguradora_ids: list[int] = fields.One2many(
        'res.partner.agente.aseguradora',
        'agente_id',
        string='Claves por Aseguradora',
    )
    cambio_promotoria_ids: list[int] = fields.One2many(
        'bca.agente.cambio.promotoria',
        'agente_id',
        string='Cambios de Promotoría',
        readonly=True,
    )

    # Roles de PÓLIZA (no excluyentes): un mismo contacto puede ser contratante
    # y asegurado a la vez, y además tener posición de red (p. ej. agente). Se
    # derivan de las pólizas (fuente única de verdad) vía estas relaciones
    # inversas; los flags almacenados sirven para filtros/visibilidad.
    bca_polizas_como_contratante: list[int] = fields.One2many(
        'bca.poliza',
        'contratante_id',
        string='Pólizas como Contratante',
    )
    bca_polizas_como_asegurado: list[int] = fields.One2many(
        'bca.poliza',
        'asegurado_id',
        string='Pólizas como Asegurado',
    )
    bca_es_contratante: bool = fields.Boolean(
        string='Es Contratante',
        compute='_compute_bca_roles_poliza',
        store=True,
    )
    bca_es_asegurado: bool = fields.Boolean(
        string='Es Asegurado',
        compute='_compute_bca_roles_poliza',
        store=True,
    )

    # Dimensión de red almacenada para filtros, agrupaciones y reportes.
    # Solo los agentes tienen Promotoría; el resto de contactos queda vacío.
    bca_promotoria_id: int = fields.Many2one(
        'res.partner',
        string='Promotoría',
        compute='_compute_promotoria_id',
        store=True,
        index=True,
        readonly=True,
    )
    bca_categoria_id: int = fields.Many2one(
        'res.partner.category',
        string='Categoría BCA',
        compute='_compute_categoria_id',
    )

    # C1: contadores para smart buttons de Pólizas y Recibos. Un mismo contacto
    # puede acumular pólizas por rol de contratante (vía contratante_id) y/o de
    # agente (vía agente vigente); el contador es la unión de ambos.
    bca_poliza_count: int = fields.Integer(
        string='# Pólizas',
        compute='_compute_bca_counts',
    )
    bca_recibo_count: int = fields.Integer(
        string='# Recibos',
        compute='_compute_bca_counts',
    )

    @api.depends('bca_tipo', 'agente_aseguradora_ids.estado')
    def _compute_bca_estado_agente(self) -> None:
        """Rollup del estado de carrera: el mejor estado en cualquier aseguradora.

        Sin claves (o no-agente) → 'prospecto'. La fuente de verdad es el puente
        res.partner.agente.aseguradora; aquí solo se proyecta para filtros/listas.
        """
        for rec in self:
            if rec.bca_tipo != 'agente':
                rec.bca_estado_agente = False
                continue
            estados = set(rec.agente_aseguradora_ids.mapped('estado'))
            rec.bca_estado_agente = next(
                (e for e in _ESTADO_AGENTE_PRIORIDAD if e in estados),
                'prospecto',
            )

    @api.depends(
        'complete_name', 'email', 'vat', 'state_id', 'country_id',
        'commercial_company_name', 'bca_tipo')
    @api.depends_context(
        'show_address', 'partner_show_db_id',
        'show_email', 'show_vat', 'lang', 'formatted_display_name')
    def _compute_display_name(self) -> None:
        """Agentes y promotorías muestran solo su nombre, sin la empresa madre.

        Odoo nativo antepone la empresa ("Contacto, Empresa") en
        ``_get_complete_name``; para la red BCA esa empresa es la promotoría/
        holding y dificulta la lectura de pólizas, recibos y reportes. Aquí se
        reutiliza la key nativa ``partner_display_name_hide_company`` sobre el
        subconjunto de la red: solo cambia lo que se ve, la relación parent_id
        (base de comisiones/reportes) permanece intacta. El resto de contactos
        conserva el comportamiento nativo.
        """
        red_bca = self.filtered(
            lambda partner: partner.bca_tipo in TIPOS_RED_NOMBRE_CORTO
        )
        if red_bca:
            super(ResPartner, red_bca.with_context(
                partner_display_name_hide_company=True
            ))._compute_display_name()
        resto = self - red_bca
        if resto:
            super(ResPartner, resto)._compute_display_name()

    @api.depends('bca_tipo', 'parent_id')
    def _compute_promotoria_id(self) -> None:
        for rec in self:
            rec.bca_promotoria_id = (
                rec.parent_id if rec.bca_tipo == 'agente' else False
            )

    @api.depends('bca_polizas_como_contratante', 'bca_polizas_como_asegurado')
    def _compute_bca_roles_poliza(self) -> None:
        """Deriva los roles de póliza (no excluyentes) desde las relaciones."""
        for rec in self:
            rec.bca_es_contratante = bool(rec.bca_polizas_como_contratante)
            rec.bca_es_asegurado = bool(rec.bca_polizas_como_asegurado)

    @staticmethod
    def _bca_norm_nombre(valor: str) -> str:
        """Normaliza un nombre para deduplicación: sin acentos, mayúsculas,
        espacios colapsados. 'Juan  Pérez ' y 'JUAN PEREZ' → 'JUAN PEREZ'."""
        if not valor:
            return ''
        sin_acentos = ''.join(
            c for c in unicodedata.normalize('NFKD', valor)
            if not unicodedata.combining(c)
        )
        return re.sub(r'\s+', ' ', sin_acentos).strip().upper()

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
        }
        for rec in self:
            xmlid = xmlid_map.get(rec.bca_tipo)
            if xmlid:
                rec.bca_categoria_id = self.env.ref(xmlid, raise_if_not_found=False)
            else:
                rec.bca_categoria_id = False

    @api.depends(
        'bca_polizas_como_contratante', 'bca_polizas_como_asegurado', 'bca_tipo')
    def _compute_bca_counts(self) -> None:
        Poliza = self.env['bca.poliza']
        Recibo = self.env['bca.recibo']
        for rec in self:
            # Unión de roles: pólizas donde es contratante y/o agente.
            rec.bca_poliza_count = Poliza.search_count([
                '|', ('contratante_id', '=', rec.id), ('agente_id', '=', rec.id),
            ])
            rec.bca_recibo_count = Recibo.search_count([
                '|',
                ('poliza_id.contratante_id', '=', rec.id),
                ('agente_poliza_id', '=', rec.id),
            ])

    def action_cambiar_promotoria(self) -> dict:
        """Abre el flujo auditado para transferir un agente."""
        self.ensure_one()
        if self.bca_tipo != 'agente':
            raise UserError(_('Solo un contacto de tipo Agente puede cambiar de Promotoría.'))
        if not (self.env.user.has_group('BCA_Seguros.group_bca_director_comercial')
                or self.env.user.has_group('BCA_Seguros.group_bca_director')):
            raise AccessError(
                _('Solo Director Comercial o Director pueden cambiar la Promotoría de un agente.')
            )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cambiar Promotoría'),
            'res_model': 'bca.wizard.cambio.promotoria',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_agente_id': self.id},
        }

    def cambiar_promotoria(self, nueva_promotoria, fecha_cambio, motivo: str) -> bool:
        """Transfer an agent through the authorized, audited workflow."""
        self.ensure_one()
        if not (self.env.user.has_group('BCA_Seguros.group_bca_director_comercial')
                or self.env.user.has_group('BCA_Seguros.group_bca_director')):
            raise AccessError(
                _('Solo Director Comercial o Director pueden cambiar la Promotoría.')
            )
        if self.bca_tipo != 'agente' or not self.parent_id:
            raise ValidationError(
                _('El Agente debe tener una Promotoría actual válida.')
            )
        if nueva_promotoria.bca_tipo != 'promotoria':
            raise ValidationError(_('La nueva entidad debe ser una Promotoría BCA.'))
        if (not nueva_promotoria.parent_id
                or nueva_promotoria.parent_id.bca_tipo != 'holding'):
            raise ValidationError(
                _('La nueva Promotoría debe pertenecer a un Holding BCA.')
            )
        if nueva_promotoria == self.parent_id:
            raise ValidationError(
                _('La nueva Promotoría debe ser diferente de la actual.')
            )
        if not motivo or not motivo.strip():
            raise ValidationError(_('El motivo del cambio es obligatorio.'))

        self.env['bca.agente.cambio.promotoria'].sudo().with_context(
            bca_from_cambio_promotoria=True,
        ).create({
            'agente_id': self.id,
            'promotoria_anterior_id': self.parent_id.id,
            'promotoria_nueva_id': nueva_promotoria.id,
            'fecha_cambio': fecha_cambio,
            'motivo': motivo.strip(),
            'usuario_id': self.env.user.id,
        })
        super().write({'parent_id': nueva_promotoria.id})
        return True

    def action_view_bca_polizas(self) -> dict:
        self.ensure_one()
        domain = [
            '|', ('contratante_id', '=', self.id), ('agente_id', '=', self.id),
        ]
        # Contexto de creación: prioriza el rol de contratante; si es un agente
        # puro, precarga el agente.
        if self.bca_tipo == 'agente' and not self.bca_es_contratante:
            context = {'default_agente_id': self.id}
        else:
            context = {'default_contratante_id': self.id}
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pólizas de %s') % self.display_name,
            'res_model': 'bca.poliza',
            'view_mode': 'list,form',
            'domain': domain,
            'context': context,
        }

    def action_view_bca_recibos(self) -> dict:
        self.ensure_one()
        domain = [
            '|',
            ('poliza_id.contratante_id', '=', self.id),
            ('agente_poliza_id', '=', self.id),
        ]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Recibos de %s') % self.display_name,
            'res_model': 'bca.recibo',
            'view_mode': 'list,form',
            'domain': domain,
        }

    def write(self, vals: dict) -> bool:
        """Protege la estructura BCA contra cambios directos silenciosos.

        Los cambios de afiliación de agentes se realizan mediante el wizard
        autorizado, que usa el contexto técnico interno y deja un registro
        inmutable en ``bca.agente.cambio.promotoria``. Los contactos normales
        conservan el comportamiento nativo de ``res.partner``.
        """
        cambios_estructura = {'bca_tipo', 'parent_id'} & set(vals)
        if cambios_estructura and not self.env.context.get(
                'bca_allow_network_structure_change'):
            for rec in self:
                if 'bca_tipo' in vals and vals['bca_tipo'] != rec.bca_tipo:
                    if rec.bca_tipo in TIPO_SELECTION or vals['bca_tipo'] in TIPO_SELECTION:
                        raise UserError(
                            _('El Tipo BCA de "%s" no se puede cambiar directamente. '
                              'Use el flujo administrativo de la red.') % rec.display_name
                        )
                if 'parent_id' in vals:
                    nuevo_parent_id = vals['parent_id'] or False
                    if rec.bca_tipo in ('agente', 'promotoria') and (
                            nuevo_parent_id != rec.parent_id.id):
                        raise UserError(
                            _('La Promotoría de "%s" no se puede cambiar directamente. '
                              'Use "Cambiar Promotoría" para dejar auditoría.')
                            % rec.display_name
                        )
        return super().write(vals)

    @api.constrains('bca_tipo', 'parent_id')
    def _check_jerarquia(self) -> None:
        """Valida la jerarquía BCA completa en cada alta o modificación.

        - Holding y aseguradora no pertenecen a la jerarquía operativa.
        - Promotoría debe pertenecer a un Holding.
        - Agente debe pertenecer a una Promotoría.
        - Los contactos sin ``bca_tipo`` conservan la jerarquía nativa.
        """
        for rec in self:
            if rec.bca_tipo == 'holding':
                if rec.parent_id:
                    raise ValidationError(
                        _('El Holding BCA "%s" no puede depender de otro contacto BCA.')
                        % rec.display_name
                    )
            elif rec.bca_tipo == 'aseguradora':
                if rec.parent_id:
                    raise ValidationError(
                        _('La Aseguradora "%s" no puede tener un parent BCA operativo.')
                        % rec.display_name
                    )
            elif rec.bca_tipo == 'promotoria':
                if not rec.parent_id:
                    raise ValidationError(
                        _('La Promotoría "%s" debe pertenecer a un Holding BCA.')
                        % rec.display_name
                    )
                if rec.parent_id.bca_tipo != 'holding':
                    raise ValidationError(
                        _('La Promotoría "%s" debe pertenecer a un Holding BCA.')
                        % rec.display_name
                    )
            elif rec.bca_tipo == 'agente':
                if not rec.parent_id:
                    raise ValidationError(
                        _('El Agente "%s" debe pertenecer a una Promotoría BCA.')
                        % rec.display_name
                    )
                if rec.parent_id.bca_tipo != 'promotoria':
                    raise ValidationError(
                        _('El Agente "%s" debe pertenecer a una Promotoría BCA.')
                        % rec.display_name
                    )

    # -------------------------------------------------------------------------
    # Independencia fiscal de la red BCA (RFC/domicilio propios por ente)
    #
    # Se conserva `parent_id` nativo para la jerarquía (los reportes de comisiones
    # derivan la promotoría por parent_id), pero se corta la sincronización nativa
    # de vat/domicilio para promotorías y agentes, que son entes fiscalmente
    # independientes. Los contactos-persona normales (sin bca_tipo) mantienen el
    # comportamiento nativo (p. ej. un empleado de una empresa SÍ comparte su RFC).
    # -------------------------------------------------------------------------
    def _fields_sync(self, values):
        """Corta el PULL y el UPSTREAM de vat/domicilio para entes independientes.

        `_fields_sync` (nativo) sincroniza en create/write: jala vat del
        commercial_partner y domicilio del padre (PULL), y empuja ambos hacia el
        padre (UPSTREAM). Para promotorías/agentes no debe ocurrir ninguna de las
        dos: conservan lo capturado en ellos mismos. El DOWNSTREAM (que un ancestro
        les escriba) se corta aparte en _commercial_sync_to_descendants (vat) y
        _update_address (domicilio), porque esas escrituras nacen en el ancestro.
        """
        if self.bca_tipo in TIPOS_FISCAL_INDEPENDIENTE:
            return
        return super()._fields_sync(values)

    def _commercial_sync_to_descendants(self, fields_to_sync=None):
        """Evita que un ancestro (holding) empuje sus commercial fields (vat) a
        promotorías/agentes.

        Reimplementa el método nativo con una sola diferencia: el recordset de
        hijos destino excluye a los entes fiscalmente independientes. El filtro
        nativo `not c.is_company` NO basta, porque una promotoría/agente persona
        física (is_company=False) quedaría dentro y sería contaminada.
        """
        commercial_partner = self.commercial_partner_id
        if fields_to_sync is None:
            fields_to_sync = self._commercial_fields()
        sync_vals = commercial_partner._convert_fields_to_values(fields_to_sync)
        sync_children = self.child_ids.filtered(
            lambda c: not c.is_company
            and c.bca_tipo not in TIPOS_FISCAL_INDEPENDIENTE
        )
        children_ids_to_sync = OrderedSet()
        for child in sync_children:
            if any(
                self.env['res.partner']._fields[fname].convert_to_write(child[fname], self)
                != sync_vals[fname]
                for fname in fields_to_sync
            ):
                children_ids_to_sync.add(child.id)
            child._commercial_sync_to_descendants(fields_to_sync)
        if children_ids_to_sync:
            children_to_sync = self.env['res.partner'].browse(children_ids_to_sync)
            children_to_sync.write(sync_vals)

    def _update_address(self, vals):
        """Evita que un ancestro escriba su domicilio sobre entes independientes.

        `_update_address` es el único punto de escritura de address fields por
        jerarquía (lo invoca _children_sync sobre los hijos type='contact', y el
        PULL de dirección). Se excluye a promotorías/agentes para que conserven su
        domicilio fiscal propio.
        """
        protegidos = self.filtered(lambda c: c.bca_tipo in TIPOS_FISCAL_INDEPENDIENTE)
        return super(ResPartner, self - protegidos)._update_address(vals)
