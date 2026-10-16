"""PASO 2: rename receipt net premium column to receipt total."""

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

    # Step 1 deployments may still have legacy prima_total in addition to the
    # new field. Preserve it as the payment amount before reusing its name.
    if _has_column(cr, 'prima_total'):
        if _has_column(cr, 'prima_total_pagada'):
            cr.execute(
                """
                UPDATE bca_recibo
                   SET prima_total_pagada = COALESCE(prima_total_pagada, prima_total)
                """
            )
            cr.execute('ALTER TABLE bca_recibo DROP COLUMN prima_total')
        else:
            cr.execute(
                'ALTER TABLE bca_recibo RENAME COLUMN prima_total TO prima_total_pagada'
            )

    if _has_column(cr, 'prima_neta') and not _has_column(cr, 'prima_total'):
        cr.execute(
            'ALTER TABLE bca_recibo RENAME COLUMN prima_neta TO prima_total'
        )
        _logger.info('PASO 2: bca_recibo.prima_neta renombrada a prima_total.')
