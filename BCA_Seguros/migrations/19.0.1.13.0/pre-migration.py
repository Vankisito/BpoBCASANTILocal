"""PASO 3: rename receipt modal premium column to net premium."""

import logging

_logger = logging.getLogger(__name__)


def _has_column(cr, column):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = 'bca_recibo' AND column_name = %s
        """,
        (column,),
    )
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return

    if _has_column(cr, 'monto_modal') and not _has_column(cr, 'prima_neta'):
        cr.execute(
            'ALTER TABLE bca_recibo RENAME COLUMN monto_modal TO prima_neta'
        )
        _logger.info('PASO 3: bca_recibo.monto_modal renombrada a prima_neta.')
