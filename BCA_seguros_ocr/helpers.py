"""Standalone resolver helpers for OCR → Odoo integration.

Adapted from BCA_Seguros/wizards/carga_portafolio.py but kept as pure
functions to avoid tight coupling.  These resolve agent, product, and
partner records from OCR-extracted data.
"""

from __future__ import annotations

import logging
from typing import Any

from odoo.exceptions import UserError
from odoo.tools import _

_logger = logging.getLogger(__name__)


def resolver_agente(env, clave_raw: str, aseguradora_id: int):
    """Resolve agent partner from ``clave_agente`` + aseguradora.

    Returns ``(partner, warning_or_None)``.  If the agent is not found,
    returns ``(None, mensaje_de_error)`` instead of raising — the caller
    decides whether to abort or let the user fix it in the wizard.
    """
    clave = str(clave_raw or "").strip()
    if not clave:
        return None, _("Clave de agente vacía.")

    Bridge = env["res.partner.agente.aseguradora"]
    base = [("aseguradora_id", "=", aseguradora_id)]

    registro = Bridge.search(base + [("clave_agente", "=", clave)], limit=1)

    # Tolerar ceros a la izquierda (el Excel pierde el padding)
    if not registro and clave.isdigit():
        objetivo = clave.lstrip("0") or "0"
        registro = Bridge.search(base).filtered(
            lambda b: (b.clave_agente or "").strip().isdigit()
            and ((b.clave_agente or "").strip().lstrip("0") or "0") == objetivo
        )[:1]

    if not registro:
        return None, _('Clave de agente "%s" no registrada en la aseguradora.') % clave

    return registro.agente_id, None


def resolver_producto(env, nombre: str, ramo: str, aseguradora_id: int):
    """Resolve product.template from name + ramo + aseguradora.

    Search order:
    1. Exact match on ``name``
    2. ``bca_nombre_archivo_aseguradora`` exact
    3. ``ilike`` on name

    Returns ``(product, warning_or_None)``.
    """
    if not nombre:
        return None, _("Nombre de producto vacío.")

    dominio_base = [
        ("bca_es_producto_seguro", "=", True),
        ("bca_aseguradora_id", "=", aseguradora_id),
    ]
    if ramo:
        dominio_base.append(("bca_ramo", "=", ramo))

    Producto = env["product.template"]
    nombre_limpio = nombre.strip()

    # 1) Exact name
    producto = Producto.search(dominio_base + [("name", "=", nombre_limpio)], limit=1)
    if producto:
        return producto, None

    # 2) bca_nombre_archivo_aseguradora
    producto = Producto.search(
        dominio_base + [("bca_nombre_archivo_aseguradora", "=", nombre_limpio)],
        limit=1,
    )
    if producto:
        return producto, None

    # 3) ilike
    producto = Producto.search(
        dominio_base + [("name", "ilike", nombre_limpio)], limit=1
    )
    if producto:
        return producto, None

    return None, _('Producto "%s" no encontrado para el ramo %s.') % (nombre, ramo)


def find_or_create_partner(env, datos: dict) -> Any:
    """Find or create a res.partner by name (and optionally vat/RFC).

    Role-agnostic: does NOT set bca_tipo.
    Adapted from carga_portafolio._find_or_create_partner.
    """
    from odoo.addons.BCA_Seguros.models.res_partner import TIPOS_RED_EXCLUIDOS_POLIZA

    nombre = datos.get("name", "").strip()
    if not nombre:
        raise UserError(_("Falta el nombre del contacto."))

    Partner = env["res.partner"]
    base = [("bca_tipo", "not in", list(TIPOS_RED_EXCLUIDOS_POLIZA))]

    # 1) By RFC (vat) — strongest match
    vat = datos.get("vat")
    if vat:
        partner = Partner.search(base + [("vat", "=ilike", vat)], limit=1)
        if partner:
            return partner

    # 2) By name case-insensitive
    partner = Partner.search(base + [("name", "=ilike", nombre)], limit=1)
    if partner:
        return partner

    # 3) Normalized name fallback
    if hasattr(Partner, "_bca_norm_nombre"):
        objetivo = Partner._bca_norm_nombre(nombre)
        primer_token = objetivo.split(" ")[0] if objetivo else ""
        if primer_token:
            candidatos = Partner.search(base + [("name", "ilike", primer_token)])
            for cand in candidatos:
                if Partner._bca_norm_nombre(cand.name) == objetivo:
                    return cand

    return Partner.create(dict(datos))


def normalizar_moneda(valor) -> str:
    """Normalize currency code from OCR text.  Defaults to MXN."""
    codigo = str(valor or "MXN").strip().upper()
    if codigo not in ("MXN", "USD"):
        codigo = "MXN"
    return codigo
