from odoo import models


class BcaReportePcaAgente(models.Model):
    _name = 'bca.reporte.pca.agente'
    _description = 'Reporte PCA por Agente'
    _auto = False

    def init(self):
        pass  # SQL view — implementar en Etapa 9
