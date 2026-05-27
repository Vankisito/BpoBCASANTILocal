from __future__ import annotations

from odoo import models, tools


class BcaReporteEstadoCartera(models.Model):
    _name = 'bca.reporte.estado.cartera'
    _description = 'Reporte Estado de Cartera'
    _auto = False

    def init(self) -> None:
        """Crea la vista SQL placeholder.

        Vista vacía (WHERE FALSE) para satisfacer la validación de registry
        de Odoo 19 que requiere que todos los modelos _auto=False tengan su
        tabla/view subyacente creada.

        Implementar la query completa en Etapa 9.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS
            SELECT 1::integer AS id
            WHERE FALSE
        """)
