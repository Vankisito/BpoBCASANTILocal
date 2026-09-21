"""Standalone resolver helpers for OCR → Odoo integration.

Adapted from BCA_Seguros/wizards/carga_portafolio.py but kept as pure
functions to avoid tight coupling.  These resolve agent, product, and
partner records from OCR-extracted data.
"""

from __future__ import annotations

import difflib
import logging
import re
import unicodedata
from typing import Any

from odoo.exceptions import UserError
from odoo.tools import _

_logger = logging.getLogger(__name__)


def _normalizar_nombre(texto: str | None) -> list[str]:
    """Lowercase + strip accents + keep alphanumeric tokens.

    Returns an ordered token list used for fuzzy word matching, e.g.
    ``"Metlife Primordial"`` → ``["metlife", "primordial"]`` and
    ``"PRIMORDIAL"`` → ``["primordial"]``.
    """
    txt = unicodedata.normalize("NFD", texto or "")
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", txt.lower())


def _tokens_coinciden(a: str, b: str) -> bool:
    """Tolerant token equality (OCR typos, e.g. METALIFE vs Metlife)."""
    return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.8


def _puntaje_tokens(tokens_busqueda: list[str], tokens_prod: list[str]) -> int:
    """How many search tokens are accounted for by distinct product tokens."""
    usados: list[str] = []
    for tb in tokens_busqueda:
        for tp in tokens_prod:
            if tp not in usados and _tokens_coinciden(tb, tp):
                usados.append(tp)
                break
    return len(usados)


# ---------------------------------------------------------------------------
# Product aliasing — ported from the Convertidor BCA helper (reglas
# confirmadas con BCA el 2026-07-09 y 2026-07-31).  El mapeo es dato, no
# lógica: estas tablas reemplazan al fuzzy para los nombres canónicos que el
# matching por similitud NO puede deducir (p. ej. METALIFE MUJER →
# Universales/Metalife Mujer).  Orden importa: prefijos más específicos van
# primero.  Un nombre sin equivalente confirmado devuelve None a propósito:
# el llamado decide si ir a fuzzy o mandar a advertencias (cero silenciosos).
# ---------------------------------------------------------------------------

# Ruido que se elimina del nombre crudo antes de comparar (traído de
# limpiar_producto_vida del convertidor, adaptado a carátulas).
# OJO: NO se elimina "TOTALIFE"/"TEMPOLIFE" aquí (en el CSV de BCA esos
# sufijos eran ruido de columna; en la carátula SON el nombre del producto).
_RUIDO_PRODUCTO = re.compile(
    r"\s*-\s*PL\s*\d+|\bPL\s*\d+\b|"
    r"\bPOLIZA DE SEGURO\b|\bVIDA INDIVIDUAL\b|\bL[IÍ]NEA GRAN VIDA\b|"
    r"\bM\.?\s*N\.?\b|\bPESOS\b|\bDLR\b|\bMN\b|\bFAMILIAR\b|\bFAM\b|"
    r"\b(?:19|20)\d{2}\b",
    re.IGNORECASE,
)


def _limpiar_nombre_producto(raw: str | None) -> str:
    """Normaliza un nombre de producto crudo de carátula.

    Quita espacios \\xa0, ruido de columna/plan/moneda (PL N, M.N.), acentos
    y colapsa espacios.  Devuelve MAYÚSCULAS sin acentos, listo para
    comparar contra los prefijos de las tablas de mapeo.
    """
    if not raw:
        return ""
    s = str(raw).replace("\xa0", " ")
    s = _RUIDO_PRODUCTO.sub(" ", s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().upper()


# Prefijos Vida (startswith) → nombre canónico en Odoo (nombre real de BD).
_MAPEO_METLIFE_VIDA = [
    # Retiro: 3 variantes + el nombre propio "MetLife Metalife Retiro"
    ("PLAN PERSONAL DE RETIRO", "MetLife Metalife Retiro"),
    ("PLAN DE RETIRO", "MetLife Metalife Retiro"),
    ("CUENTA ESPECIAL AHORRO", "MetLife Metalife Retiro"),
    ("METALIFE RETIRO", "MetLife Metalife Retiro"),
    # Familia Metalife (carátulas IV1360ME)
    ("METALIFE TU FUTURO", "MetLife Metalife tu Futuro"),
    ("METALIFE EDUCACION", "Metlife Educalife"),
    ("METALIFE MUJER", "MetLife Metalife Mujer"),
    # Productos clásicos (confirmado con BCA)
    ("ORDINARIO DE VIDA", "MetLife TotalLife"),
    ("VIDA PAGOS LIMITADOS", "MetLife Vida Pagos"),
    ("VIDA PAGOS", "MetLife Vida Pagos"),
    ("PERFECTLIFE", "MetLife PerfectLife"),
    ("PERFECT LIFE", "MetLife PerfectLife"),
    ("FLEXILIFE", "Metlife FlexiLife"),
    ("FLEXI LIFE", "Metlife FlexiLife"),
    ("HORIZONTE", "Metlife Horizonte"),
    ("TOTALIFE", "MetLife TotalLife"),
    ("TEMPOLIFE", "MetLife TempoLife"),
    ("TEMPORAL", "MetLife TempoLife"),
]


def mapear_producto_metlife(raw: str | None, ramo: str | None) -> str | None:
    """Devuelve el nombre canónico del producto MetLife en Odoo.

    ``ramo`` discrimina las reglas GMM de las de Vida.  Va a los prefijos de
    la carátula limpia; ``None`` significa "sin equivalente confirmado".

    Casos especiales confirmados con BCA/Rafael 2026-07-31: la familia
    TEMPORAL con EDUCALIFE o GRANDES SUMAS es TempoLife GP/RP; el resto de
    TEMPORAL/TEMPOLIFE simple es TempoLife.
    """
    c = _limpiar_nombre_producto(raw)
    if not c:
        return None

    if ramo == "gmm":
        if "GRUPO VIDA" in c:
            return "Grupo vida"
        if "MEDICALIFE" in c:
            return "MetLife MedicaLife"
        if "PRIMORDIAL" in c:
            return "MetLife Primordial"
        return None

    if (c.startswith("TEMPORAL") or c.startswith("TEMPOLIFE")) and (
        "EDUCALIFE" in c or "GRANDES SUMAS" in c
    ):
        return "MetLife TempoLife GP/RP"

    for prefijo, producto in _MAPEO_METLIFE_VIDA:
        if c.startswith(prefijo):
            return producto
    return None


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

    Search cascade (progressive relaxation):
    1. Exact ``name`` / ``bca_nombre_archivo_aseguradora``
    2. Canonical MetLife rules (semantic equivalences confirmed with BCA,
       ported from the Convertidor helper), e.g. ``METALIFE EDUCACION`` →
       ``Metlife Educalife``, ``GASTOS MEDICOS MEDICALIFE FAM.`` →
       ``MetLife MedicaLife``
    3. Case-insensitive substring (``ilike``) on both fields
    4. Fuzzy word matching: every normalized OCR token must map to a
       product-name token (case-, accent- and typo-insensitive), e.g.
       carátula ``METALIFE UNIVERSALES`` → producto ``MetLife Universales``.

    ``ramo`` and ``aseguradora_id`` are hard filters. When several candidates
    tie on token overlap, the
    shortest name (most specific) wins and a warning flags the ambiguity.

    Returns ``(product, warning_or_None)`` — never raises, the caller
    decides how to surface a missing product.
    """
    if not nombre:
        return None, _("Nombre de producto vacío.")

    Producto = env["product.template"]
    nombre_limpio = nombre.strip()
    dominio_base = [
        ("bca_es_producto_seguro", "=", True),
        ("bca_aseguradora_id", "=", aseguradora_id),
    ]
    if ramo:
        dominio_base.append(("bca_ramo", "=", ramo))

    # 1) Exact match (whole search domain)
    producto = Producto.search(
        dominio_base
        + [
            "|",
            ("name", "=", nombre_limpio),
            ("bca_nombre_archivo_aseguradora", "=", nombre_limpio),
        ],
        limit=1,
    )
    if producto:
        return producto, None

    # 1.5) Reglas canónicas MetLife (portadas del Convertidor BCA) — corren
    # ANTES del fuzzy porque codifican equivalencias semánticas que la
    # similitud de tokens NO puede deducir (p. ej. METALIFE EDUCACION →
    # EducaLife, ORDINARIO DE VIDA → TotalLife). Si la regla acierta pero el
    # producto no existe en el catálogo, se reporta en vez de seguir a fuzzy
    # (cero silenciosos).
    canonico = mapear_producto_metlife(nombre_limpio, ramo)
    if canonico:
        producto = Producto.search(
            dominio_base + [("name", "=ilike", canonico)], limit=1
        )
        if producto:
            return producto, None
        return (
            None,
            _(
                'El nombre "%s" corresponde al producto "%s" según la regla, '
                "pero ese producto no existe en el catálogo de la aseguradora."
            )
            % (nombre_limpio, canonico),
        )

    candidatos = _colectar_candidatos(
        Producto, dominio_base, ramo, nombre_limpio, aseguradora_id
    )

    if not candidatos:
        return None, _('Producto "%s" no encontrado para el ramo %s.') % (
            nombre,
            ramo,
        )

    mejor, ambiguos = _elegir_mejor(candidatos, nombre_limpio)
    advertencias = []
    if ambiguos:
        otros = ", ".join(p.display_name for p in ambiguos)
        advertencias.append(
            _('Match ambiguo para "%s": podría ser también %s.') % (nombre, otros)
        )
    return mejor, ("\n".join(advertencias) if advertencias else None)


def _colectar_candidatos(
    Producto, dominio: list, ramo: str, nombre: str, aseguradora_id: int
) -> list:
    """Assemble candidates while preserving hard ramo filtering."""
    return _candidatos_pool(Producto, dominio, nombre)


def _candidatos_pool(Producto, dominio: list, nombre: str) -> list:
    """ilike substring hits merged with fuzzy word-only hits."""
    candidatos = __buscar_ilike(Producto, dominio, nombre)
    for prod in _candidatos_fuzzy(Producto, dominio, nombre):
        if prod.id not in [c.id for c in candidatos]:
            candidatos.append(prod)
    return candidatos


def __buscar_ilike(Producto, dominio: list, nombre: str) -> list:
    return list(
        Producto.search(
            dominio
            + [
                "|",
                ("name", "ilike", nombre),
                ("bca_nombre_archivo_aseguradora", "ilike", nombre),
            ]
        )
    )


def _candidatos_fuzzy(Producto, dominio: list, nombre: str) -> list:
    """Products whose normalized tokens cover every OCR token.

    Skips exact/substring-only hits (handled upstream) to reduce noise.
    """
    tokens = _normalizar_nombre(nombre)
    if not tokens:
        return []
    return [
        prod
        for prod in Producto.search(dominio)
        if _puntaje_tokens(tokens, _normalizar_nombre(prod.display_name or prod.name))
        == len(tokens)
    ]


def _elegir_mejor(candidatos: list, nombre: str):
    """Pick best fuzzy candidate; return (product, list_ambiguos).

    Score = number of OCR tokens covered; tie-break by shortest name.
    """
    tokens = _normalizar_nombre(nombre)
    puntuados = []
    for prod in candidatos:
        prod_tokens = _normalizar_nombre(prod.display_name or prod.name)
        puntuados.append((_puntaje_tokens(tokens, prod_tokens), len(prod_tokens), prod))
    puntuados.sort(key=lambda t: (-t[0], t[1]))
    mejor = puntuados[0][2]
    mejor_id = mejor.id
    ambiguos = [
        p
        for c, _, p in puntuados[1:]
        if c == puntuados[0][0] and p.id != mejor_id
    ]
    return mejor, ambiguos


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
