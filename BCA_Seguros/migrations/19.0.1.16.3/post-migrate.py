"""Move MetLife payment references from res.partner into bca.poliza.

Before 19.0.1.16.3 the payment references (bca_ref_*, bca_fondo_*) lived on
the contratante (res.partner). From this version they are first-class fields
of the policy (bca.poliza). The ORM creates the new columns on bca.poliza
before post-migrate runs, so a single SQL backfill copies each contratante's
references onto all of their policies.
"""

import logging

_logger = logging.getLogger(__name__)


_FIELD_PAIRS = (
    ("bca_ref_prima_basica_trad", "bca_ref_prima_basica_trad"),
    ("bca_ref_prima_medica", "bca_ref_prima_medica"),
    ("bca_fondo_variable", "bca_fondo_variable"),
    ("bca_fondo_fijo", "bca_fondo_fijo"),
    ("bca_fondo_variable_ppr", "bca_fondo_variable_ppr"),
    ("bca_fondo_fijo_ppr", "bca_fondo_fijo_ppr"),
    ("bca_fondo_variable_cpea", "bca_fondo_variable_cpea"),
    ("bca_fondo_fijo_cpea", "bca_fondo_fijo_cpea"),
)


def _has_column(cr, table, column):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return
    if not _has_column(cr, "res_partner", "bca_ref_prima_basica_trad"):
        return
    if not _has_column(cr, "bca_poliza", "bca_ref_prima_basica_trad"):
        return

    assignments = ", ".join(
        "%s = res_partner.%s" % (dst, src)
        for src, dst in _FIELD_PAIRS
    )
    cr.execute(
        """
        UPDATE bca_poliza
           SET %s
          FROM res_partner
         WHERE bca_poliza.contratante_id = res_partner.id
        """
        % assignments
    )
    _logger.info(
        "BCA 19.0.1.16.3: referencias MetLife copiadas de contratantes "
        "a %s pólizas.",
        cr.rowcount,
    )