"""Move MetLife payment references from res.partner into bca.poliza.

Pre-19.0.1.16.3 the payment references (bca_ref_*, bca_fondo_*) lived on the
contratante (res.partner). From 19.0.1.16.3 they are first-class fields of the
policy (bca.poliza).

This must run as pre-migration, not post-migrate: on upgrade the ORM drops the
columns of removed model fields *before* post-migrate scripts run, so a
post-migrate script would see the source columns already gone and copy
nothing. In pre-migration the source columns still exist, so we create the
target columns and backfill each contratante's references onto their policies
before the ORM drops the source.
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


def _add_text_column(cr, column):
    if _has_column(cr, "bca_poliza", column):
        return
    cr.execute('ALTER TABLE bca_poliza ADD COLUMN %s varchar' % column)


def migrate(cr, version):
    if not version:
        return
    source = _FIELD_PAIRS[0][0]
    if not _has_column(cr, "res_partner", source):
        _logger.info(
            "BCA 19.0.1.16.4: sin columna %s en res_partner, "
            "no hay refs MetLife que migrar.",
            source,
        )
        return

    for _src, dst in _FIELD_PAIRS:
        _add_text_column(cr, dst)

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
        "BCA 19.0.1.16.4: referencias MetLife copiadas de contratantes "
        "a %s pólizas.",
        cr.rowcount,
    )