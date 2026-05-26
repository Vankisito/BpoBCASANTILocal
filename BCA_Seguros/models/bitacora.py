from odoo import models


class BcaBitacoraImportacion(models.Model):
    _name = 'bca.bitacora.importacion'
    _description = 'Bitácora de Importación de Cobranza'


class BcaBitacoraLinea(models.Model):
    _name = 'bca.bitacora.linea'
    _description = 'Línea de Bitácora de Importación'
