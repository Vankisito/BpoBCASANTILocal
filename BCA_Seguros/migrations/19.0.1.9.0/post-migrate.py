"""Independencia fiscal de la red BCA: limpia RFC/domicilio heredados.

Antes de 19.0.1.9.0, promotorías y agentes heredaban el RFC (`vat`) y el domicilio
de su ancestro comercial por la sincronización nativa de res.partner. Desde esta
versión esa sincronización se corta para esos entes (ver overrides en
models/res_partner.py), pero los registros YA creados quedaron con el dato
contaminado. Esta migración los normaliza:

1) RFC (`vat`): para cada promotoría/agente cuyo `vat` coincide con el de su
   entidad comercial (señal de herencia), intenta recuperar el RFC PROPIO desde el
   candidato de origen (`hr.applicant.bca_rfc`). Si hay un valor propio y distinto,
   lo usa; si no, deja el `vat` en blanco para forzar recaptura manual (no se
   conserva un RFC ajeno, que sería un error silencioso en CFDI).
2) Domicilio: limpia los campos de dirección que coincidan con los del padre
   (heredados). Hoy no hay domicilios capturados, pero se incluye por robustez.

Los entes cuyo dato ya difiere del ancestro (RFC/domicilio propios) no se tocan.
En instalación limpia (`-i`) no hay datos previos, así que solo aplica en upgrade.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# Campos de dirección que Odoo sincroniza desde el padre (ADDRESS_FIELDS nativo).
_ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id')


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    Partner = env['res.partner']
    Applicant = env['hr.applicant']

    entes = Partner.search([('bca_tipo', 'in', ('promotoria', 'agente'))])

    rfc_recuperados = []
    rfc_limpiados = []
    domicilios_limpiados = []

    for ente in entes:
        commercial = ente.commercial_partner_id
        # Una entidad comercial propia (persona moral) nunca heredó su RFC.
        heredo_rfc = (
            commercial != ente
            and ente.vat
            and commercial.vat
            and ente.vat == commercial.vat
        )
        if heredo_rfc:
            propio = _rfc_propio_de_applicant(Applicant, ente, commercial.vat)
            if propio:
                ente.vat = propio
                rfc_recuperados.append((ente.id, propio))
            else:
                ente.vat = False
                rfc_limpiados.append(ente.id)

        # Domicilio heredado del padre: limpiar los campos que coincidan.
        parent = ente.parent_id
        if parent:
            a_limpiar = {
                fname: False
                for fname in _ADDRESS_FIELDS
                if ente[fname] and ente[fname] == parent[fname]
            }
            if a_limpiar:
                ente.write(a_limpiar)
                domicilios_limpiados.append(ente.id)

    _logger.info(
        "BCA independencia fiscal: RFC recuperados desde applicant=%s; "
        "RFC limpiados para recaptura manual=%s; domicilios limpiados=%s.",
        rfc_recuperados, rfc_limpiados, domicilios_limpiados,
    )


def _rfc_propio_de_applicant(Applicant, ente, vat_ancestro):
    """Devuelve el RFC propio del ente tomado de hr.applicant.bca_rfc, si existe y
    difiere del RFC del ancestro (señal de que es el valor real y no el heredado)."""
    applicants = Applicant.search([('partner_id', '=', ente.id)])
    for applicant in applicants:
        rfc = (applicant.bca_rfc or '').strip()
        if rfc and rfc != vat_ancestro:
            return rfc
    return False
