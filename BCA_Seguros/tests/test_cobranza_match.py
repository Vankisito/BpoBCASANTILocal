from __future__ import annotations

from odoo.tests.common import TransactionCase, tagged

from .test_cobranza_fifo import _CobranzaFixtures, _csv_b64
from odoo.addons.BCA_Seguros.parsers.metlife_lsp import COLUMNAS_LSP
from odoo.addons.BCA_Seguros.parsers.metlife_gcaye import COLUMNAS_GCAYE


@tagged('BCA_Seguros')
class TestCobranzaMatchVigencia(_CobranzaFixtures):
    """R-COB-11: match por póliza + vigencia (sin prima).

    Criterios de aceptación del plan:
    1. Doble subida → 1 cobro aplicado + 1 rechazado con motivo.
    2. Vigencia distinta → rechazada con motivo, recibo intacto.
    3. Fila legítima → se aplica con normalidad.
    4. GMM: mismos casos + anulaciones siguen omitiéndose.
    """

    def test_doble_subida_misma_vigencia_no_duplica(self) -> None:
        """Subir dos veces la misma póliza+vigencia → 1 aplicado + 1 sin_coincidencia."""
        pol = self._poliza('PV-DUP')
        filas = [
            self._fila_vida('PV-DUP'),
            self._fila_vida('PV-DUP'),  # segunda vez → sin coincidencia
        ]
        bitacora = self._procesar(COLUMNAS_LSP, filas)

        self.assertEqual(bitacora.recibos_aplicados, 1)
        self.assertEqual(bitacora.recibos_sin_coincidencia, 1)
        marcas = bitacora.linea_ids.mapped('marca')
        self.assertIn('aplicado', marcas)
        self.assertIn('sin_coincidencia', marcas)
        # Solo 1 recibo pagado
        pagados = pol.recibo_ids.filtered(lambda r: r.estado == 'pagado')
        self.assertEqual(len(pagados), 1)

    def test_vigencia_distinta_rechazada(self) -> None:
        """Fila con vigencia distinta al recibo → sin_coincidencia, recibo intacto."""
        pol = self._poliza('PV-VIG')
        # La póliza mensual genera recibos con vigencia 01/XX–01/XX+1
        # Enviamos vigencia incorrecta
        filas = [
            self._fila_vida('PV-VIG', vigencia_desde='15/03/2025', vigencia_hasta='15/04/2025'),
        ]
        bitacora = self._procesar(COLUMNAS_LSP, filas)

        self.assertEqual(bitacora.recibos_aplicados, 0)
        self.assertEqual(bitacora.recibos_sin_coincidencia, 1)
        linea = bitacora.linea_ids[0]
        self.assertEqual(linea.marca, 'sin_coincidencia')
        self.assertIn('Sin coincidencia', linea.mensaje)
        # Recibo sigue pendiente
        pendientes = pol.recibo_ids.filtered(lambda r: r.estado == 'pendiente')
        self.assertTrue(pendientes)

    def test_fila_legitima_se_aplica(self) -> None:
        """Fila con vigencia correcta → se aplica normalmente."""
        pol = self._poliza('PV-OK')
        # Recibo 1 tiene vigencia 01/01/2025–01/02/2025
        filas = [self._fila_vida('PV-OK')]
        bitacora = self._procesar(COLUMNAS_LSP, filas)

        self.assertEqual(bitacora.recibos_aplicados, 1)
        self.assertEqual(bitacora.recibos_sin_coincidencia, 0)
        pagados = pol.recibo_ids.filtered(lambda r: r.estado == 'pagado')
        self.assertEqual(len(pagados), 1)
        self.assertEqual(pagados.numero_recibo, 1)

    def test_gmm_doble_subida_no_duplica(self) -> None:
        """GMM: doble subida → 1 aplicado + 1 sin_coincidencia."""
        pol = self._poliza('PG-DUP', ramo='gmm')
        filas = [
            self._fila_gmm('PG-DUP'),
            self._fila_gmm('PG-DUP'),  # segunda vez
        ]
        bitacora = self._procesar(COLUMNAS_GCAYE, filas, ramo='gmm')

        self.assertEqual(bitacora.recibos_aplicados, 1)
        self.assertEqual(bitacora.recibos_sin_coincidencia, 1)

    def test_gmm_anulaciones_siguen_omitiendose(self) -> None:
        """GMM: anulaciones se omiten Y vigencia incorrecta → sin_coincidencia."""
        pol = self._poliza('PG-MIX', ramo='gmm')
        filas = [
            self._fila_gmm('PG-MIX'),
            self._fila_gmm('PG-MIX', estatus_pago='anulado'),
            self._fila_gmm('PG-MIX', vigencia_desde='15/03/2025', vigencia_hasta='15/04/2025'),
        ]
        bitacora = self._procesar(COLUMNAS_GCAYE, filas, ramo='gmm')

        self.assertEqual(bitacora.recibos_aplicados, 1)
        self.assertEqual(bitacora.anulaciones_ignoradas, 1)
        self.assertEqual(bitacora.recibos_sin_coincidencia, 1)

    def test_mensaje_incluye_recibos_pendientes(self) -> None:
        """El mensaje de sin_coincidencia lista los recibos pendientes reales."""
        pol = self._poliza('PV-MSG')
        filas = [
            self._fila_vida('PV-MSG', vigencia_desde='15/03/2025', vigencia_hasta='15/04/2025'),
        ]
        bitacora = self._procesar(COLUMNAS_LSP, filas)

        linea = bitacora.linea_ids[0]
        self.assertEqual(linea.marca, 'sin_coincidencia')
        self.assertIn('Recibos pendientes:', linea.mensaje)
        # Debe mencionar al menos un recibo pendiente
        self.assertIn('PV-MSG', linea.mensaje)
