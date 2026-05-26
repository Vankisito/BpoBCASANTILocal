from odoo import models


class BcaReporteEstadoCartera(models.Model):
    _name = 'bca.reporte.estado.cartera'
    _description = 'Reporte Estado de Cartera'
    _auto = False

    def init(self):
        pass  # SQL view — implementar en Etapa 9
