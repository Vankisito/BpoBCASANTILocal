"""Traslada las referencias de pago MetLife de res.partner a bca.poliza.

Antes de 19.0.1.16.4 las referencias de cobro vivían en el contacto
contratante. Ahora son datos de la póliza. La migración copia los valores
legacy a cada póliza del contratante, solo en campos vacíos y según el ramo:
Vida = TRAD + fondos; GMM = referencia médica.

Los campos legacy del partner se conservan ocultos una versión para
migración/rollback; esta migración NO los borra.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    actualizadas = env['bca.poliza']._migrar_referencias_pago_legacy()
    _logger.info(
        "BCA referencias de pago: %s pólizas actualizadas desde res.partner.",
        actualizadas,
    )
