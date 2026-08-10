"""Backfill stored Promotoría dimensions introduced in 19.0.1.10.0."""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})

    # The ORM creates both columns before post-migrate runs. Use SQL for the
    # backfill so existing rows are repaired in one transaction and historical
    # receipt snapshots remain untouched.
    cr.execute(
        """
        UPDATE res_partner AS agent
           SET bca_promotoria_id = CASE
               WHEN agent.bca_tipo = 'agente' THEN agent.parent_id
               ELSE NULL
           END
        """
    )
    partners_updated = cr.rowcount

    cr.execute(
        """
        UPDATE bca_poliza AS poliza
           SET promotoria_id = agent.parent_id
          FROM res_partner AS agent
         WHERE poliza.agente_id = agent.id
        """
    )
    policies_updated = cr.rowcount

    Partner = env['res.partner']
    invalid_agents = Partner.search([
        ('bca_tipo', '=', 'agente'),
        '|',
        ('parent_id', '=', False),
        ('parent_id.bca_tipo', '!=', 'promotoria'),
    ])
    invalid_promotorias = Partner.search([
        ('bca_tipo', '=', 'promotoria'),
        '|',
        ('parent_id', '=', False),
        ('parent_id.bca_tipo', '!=', 'holding'),
    ])
    if invalid_agents or invalid_promotorias:
        _logger.warning(
            'BCA 19.0.1.10.0: jerarquía inválida detectada; agentes=%s, '
            'promotorias=%s. Los datos se conservan para remediación explícita.',
            invalid_agents.ids,
            invalid_promotorias.ids,
        )

    env.invalidate_all()
    _logger.info(
        'BCA 19.0.1.10.0: backfill completado; partners=%s, polizas=%s.',
        partners_updated,
        policies_updated,
    )