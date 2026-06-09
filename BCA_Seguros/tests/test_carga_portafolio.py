from __future__ import annotations

import base64
import io
from datetime import date, timedelta

import openpyxl

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

# Encabezados mínimos por hoja para los fixtures (subset del layout real).
HEADERS_VIDA = [
    'Póliza', 'Producto', 'Clave de Agente', 'Nombre del Contratante',
    'Nombre del Asegurado', 'Moneda', 'Fecha inicio Vigencia',
    'Fecha Fin Vigencia', 'Frecuencia de Pago', 'Prima de Riesgo Anual',
    'Pagado Hasta', 'Estatus de Póliza', 'Estatus de Pago', 'R.F.C. Contratante',
    'Nombre del Beneficiario 1', 'Parentesco 1', '% al que tiene Derecho 1',
    'Nombre del Beneficiario 2', 'Parentesco 2', '% al que tiene Derecho 2',
]
HEADERS_GMM = [
    'Poliza actual', 'Producto', 'Clave de Agente', 'Nombre del Contratante',
    'Moneda', 'Fecha inicio Vigencia', 'Fecha Fin Vigencia',
    'Frecuencia de Pago', 'Prima de Riesgo Anual', 'Deducible', 'Coaseguro',
    'Pagado Hasta', 'Nombre del Asegurado 1', 'Parentesco 1',
    'Fecha de nacimiento (Asegurado 1)',
]


def _build_xlsx(sheets: dict) -> bytes:
    """sheets = {nombre: (headers, [fila_dict, ...])}. Encabezados en fila 2,
    tipos en fila 3, datos desde fila 4 (estructura del layout real)."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for nombre, (headers, filas) in sheets.items():
        ws = wb.create_sheet(nombre)
        ws.append(['Layout %s' % nombre])              # fila 1: título
        ws.append(headers)                              # fila 2: encabezados
        ws.append(['tipo'] * len(headers))              # fila 3: tipos
        for fila in filas:                              # fila 4+: datos
            ws.append([fila.get(h, '') for h in headers])
    buffer = io.BytesIO()
    wb.save(buffer)
    return base64.b64encode(buffer.getvalue())


class _PortafolioFixtures(TransactionCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        Partner = cls.env['res.partner']
        cls.aseguradora = cls.env.ref('BCA_Seguros.partner_metlife')
        cls.holding = Partner.create({'name': 'Holding P', 'bca_tipo': 'holding'})
        cls.promotoria = Partner.create({
            'name': 'Promotoría P', 'bca_tipo': 'promotoria',
            'parent_id': cls.holding.id,
        })
        cls.agente = Partner.create({
            'name': 'Agente P', 'bca_tipo': 'agente',
            'parent_id': cls.promotoria.id,
        })
        cls.env['res.partner.agente.aseguradora'].create({
            'agente_id': cls.agente.id,
            'aseguradora_id': cls.aseguradora.id,
            'clave_agente': 'A100',
            'estado': 'clave_definitiva',
        })
        cls.producto_vida = cls.env['product.template'].create({
            'name': 'TempoLife Portafolio',
            'bca_es_producto_seguro': True,
            'bca_aseguradora_id': cls.aseguradora.id,
            'bca_ramo': 'vida',
        })
        cls.producto_gmm = cls.env['product.template'].create({
            'name': 'GMM Portafolio',
            'bca_es_producto_seguro': True,
            'bca_aseguradora_id': cls.aseguradora.id,
            'bca_ramo': 'gmm',
        })

    def _wizard(self, archivo: bytes, modo: str = 'crear_actualizar'):
        return self.env['bca.wizard.carga.portafolio'].create({
            'archivo': archivo,
            'nombre_archivo': 'portafolio.xlsx',
            'aseguradora_id': self.aseguradora.id,
            'modo': modo,
        })

    def _fila_vida(self, **ov) -> dict:
        base = {
            'Póliza': 'PV-001', 'Producto': 'TempoLife Portafolio',
            'Clave de Agente': 'A100', 'Nombre del Contratante': 'Juan Pérez',
            'Nombre del Asegurado': 'Juan Pérez', 'Moneda': 'MXN',
            'Fecha inicio Vigencia': '01/01/2025', 'Fecha Fin Vigencia': '01/01/2027',
            'Frecuencia de Pago': 'Mensual', 'Prima de Riesgo Anual': '12,000.00',
            'Pagado Hasta': '', 'Estatus de Póliza': 'Vigente',
            'Estatus de Pago': 'Al corriente', 'R.F.C. Contratante': 'PEPJ800101AAA',
        }
        base.update(ov)
        return base

    def _fila_gmm(self, **ov) -> dict:
        base = {
            'Poliza actual': 'PG-001', 'Producto': 'GMM Portafolio',
            'Clave de Agente': 'A100', 'Nombre del Contratante': 'Ana López',
            'Moneda': 'MXN', 'Fecha inicio Vigencia': '01/01/2025',
            'Fecha Fin Vigencia': '01/01/2026', 'Frecuencia de Pago': 'Anual',
            'Prima de Riesgo Anual': '20,000.00', 'Deducible': '30,000.00',
            'Coaseguro': '10',
        }
        base.update(ov)
        return base


@tagged('BCA_Seguros')
class TestCargaPortafolioValidacion(_PortafolioFixtures):
    """Fase VALIDAR: estructura y dry-run sin tocar BD."""

    def test_validar_sin_hoja_soportada(self) -> None:
        archivo = _build_xlsx({'OTRA': (['x'], [{'x': 1}])})
        with self.assertRaises(UserError):
            self._wizard(archivo).action_validar()

    def test_validar_columna_faltante(self) -> None:
        headers = [h for h in HEADERS_VIDA if h != 'Producto']
        archivo = _build_xlsx({'VIDA': (headers, [self._fila_vida()])})
        with self.assertRaises(UserError):
            self._wizard(archivo).action_validar()

    def test_validar_no_crea_polizas(self) -> None:
        archivo = _build_xlsx({'VIDA': (HEADERS_VIDA, [self._fila_vida()])})
        wizard = self._wizard(archivo)
        wizard.action_validar()
        self.assertEqual(wizard.state, 'validado')
        self.assertEqual(wizard.total_filas, 1)
        self.assertFalse(self.env['bca.poliza'].search([('name', '=', 'PV-001')]))

    def test_validar_marca_agente_inexistente(self) -> None:
        fila = self._fila_vida(**{'Clave de Agente': 'NOPE'})
        archivo = _build_xlsx({'VIDA': (HEADERS_VIDA, [fila])})
        wizard = self._wizard(archivo)
        wizard.action_validar()
        self.assertEqual(wizard.rechazadas, 1)


@tagged('BCA_Seguros')
class TestCargaPortafolioGrabado(_PortafolioFixtures):
    """Fase GRABAR: creación, corte por Pagado Hasta, beneficiarios, duplicados."""

    def _grabar(self, sheets: dict, modo: str = 'crear_actualizar'):
        wizard = self._wizard(_build_xlsx(sheets), modo=modo)
        wizard.action_validar()
        wizard.action_grabar()
        return wizard

    def test_crea_vida_y_gmm(self) -> None:
        wizard = self._grabar({
            'VIDA': (HEADERS_VIDA, [self._fila_vida()]),
            'GMM': (HEADERS_GMM, [self._fila_gmm()]),
        })
        self.assertEqual(wizard.creadas, 2)
        vida = self.env['bca.poliza'].search([('name', '=', 'PV-001')])
        gmm = self.env['bca.poliza'].search([('name', '=', 'PG-001')])
        self.assertEqual(vida.agente_id, self.agente)
        self.assertEqual(vida.estado, 'activa')
        self.assertEqual(vida.contratante_id.name, 'Juan Pérez')
        self.assertAlmostEqual(gmm.coaseguro, 0.10, places=2)
        self.assertEqual(gmm.estado, 'activa')

    def test_pagado_hasta_genera_solo_recibos_posteriores(self) -> None:
        fila = self._fila_vida(**{'Pagado Hasta': '30/06/2025'})
        self._grabar({'VIDA': (HEADERS_VIDA, [fila])})
        vida = self.env['bca.poliza'].search([('name', '=', 'PV-001')])
        self.assertEqual(vida.pagado_hasta_inicial, date(2025, 6, 30))
        self.assertTrue(vida.recibo_ids)
        primera = min(vida.recibo_ids.mapped('fecha_desde'))
        self.assertGreaterEqual(primera, date(2025, 6, 30),
                                'No deben generarse recibos antes del corte.')
        # pagado_hasta operativo sigue vacío (no hay recibos pagados).
        self.assertFalse(vida.pagado_hasta)

    def test_beneficiarios_vida_y_dependientes_gmm(self) -> None:
        fila_v = self._fila_vida(**{
            'Nombre del Beneficiario 1': 'Hijo Uno', 'Parentesco 1': 'Hijo',
            '% al que tiene Derecho 1': '50',
            'Nombre del Beneficiario 2': 'Hija Dos', 'Parentesco 2': 'Hija',
            '% al que tiene Derecho 2': '50',
        })
        fila_g = self._fila_gmm(**{
            'Nombre del Asegurado 1': 'Dependiente Uno', 'Parentesco 1': 'Cónyuge',
            'Fecha de nacimiento (Asegurado 1)': '15/05/1990',
        })
        self._grabar({
            'VIDA': (HEADERS_VIDA, [fila_v]),
            'GMM': (HEADERS_GMM, [fila_g]),
        })
        vida = self.env['bca.poliza'].search([('name', '=', 'PV-001')])
        gmm = self.env['bca.poliza'].search([('name', '=', 'PG-001')])
        self.assertEqual(len(vida.beneficiario_ids), 2)
        self.assertAlmostEqual(
            sum(vida.beneficiario_ids.mapped('porcentaje')), 100.0, places=2)
        self.assertEqual(len(gmm.beneficiario_ids), 1)
        self.assertEqual(gmm.beneficiario_ids.fecha_nacimiento, date(1990, 5, 15))

    def test_modo_solo_crear_rechaza_duplicado(self) -> None:
        sheets = {'VIDA': (HEADERS_VIDA, [self._fila_vida()])}
        self._grabar(sheets)
        wizard2 = self._grabar(sheets, modo='solo_crear')
        self.assertEqual(wizard2.creadas, 0)
        self.assertEqual(wizard2.rechazadas, 1)

    def test_fila_con_error_no_detiene_proceso(self) -> None:
        ok = self._fila_vida(**{'Póliza': 'PV-OK'})
        malo = self._fila_vida(**{'Póliza': 'PV-MAL', 'Clave de Agente': 'NOPE'})
        wizard = self._grabar({'VIDA': (HEADERS_VIDA, [ok, malo])})
        self.assertEqual(wizard.creadas, 1)
        self.assertEqual(wizard.rechazadas, 1)
        self.assertTrue(self.env['bca.poliza'].search([('name', '=', 'PV-OK')]))
        self.assertFalse(self.env['bca.poliza'].search([('name', '=', 'PV-MAL')]))


@tagged('BCA_Seguros')
class TestPlantillaDescarga(_PortafolioFixtures):
    """Descarga de la plantilla y round-trip: lo que genera el wizard debe
    ser re-validable por el propio wizard sin errores estructurales."""

    def test_descargar_devuelve_act_url_y_adjunto(self) -> None:
        wizard = self._wizard(_build_xlsx({'VIDA': (HEADERS_VIDA, [self._fila_vida()])}))
        accion = wizard.action_descargar_plantilla()
        self.assertEqual(accion['type'], 'ir.actions.act_url')
        self.assertEqual(accion['target'], 'download')
        self.assertIn('/web/content/', accion['url'])

        att_id = int(accion['url'].split('/web/content/')[1].split('?')[0])
        adjunto = self.env['ir.attachment'].browse(att_id)
        self.assertEqual(adjunto.name, 'plantilla_portafolio_BCA.xlsx')
        self.assertEqual(
            adjunto.mimetype,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertTrue(adjunto.datas)
        # Atado al transient para que el vacuum lo purgue.
        self.assertEqual(adjunto.res_model, 'bca.wizard.carga.portafolio')
        self.assertEqual(adjunto.res_id, wizard.id)

    def test_round_trip_plantilla_es_validable(self) -> None:
        # La plantilla generada se vuelve a cargar: la estructura (hojas VIDA y
        # GMM, columnas requeridas) debe ser válida y no lanzar.
        origen = self._wizard(_build_xlsx({'VIDA': (HEADERS_VIDA, [self._fila_vida()])}))
        accion = origen.action_descargar_plantilla()
        att_id = int(accion['url'].split('/web/content/')[1].split('?')[0])
        datas = self.env['ir.attachment'].browse(att_id).datas

        wizard = self._wizard(datas)
        wizard.action_validar()
        self.assertEqual(wizard.state, 'validado')
        # 2 filas de ejemplo por hoja (VIDA + GMM).
        self.assertEqual(wizard.total_filas, 4)


@tagged('BCA_Seguros')
class TestEstatusPagoComputed(_PortafolioFixtures):
    """estatus_pago derivado de pagado_hasta/pagado_hasta_inicial vs hoy."""

    def _poliza_activa(self, **ov):
        vals = {
            'name': 'POL-EST', 'aseguradora_id': self.aseguradora.id,
            'producto_id': self.producto_vida.id, 'agente_id': self.agente.id,
            'contratante_id': self.env['res.partner'].create({
                'name': 'C Est', 'bca_tipo': 'contratante'}).id,
            'fecha_inicio': date(2025, 1, 1), 'fecha_fin': date(2027, 1, 1),
            'periodicidad': 'mensual', 'prima_anual': 12000.0,
        }
        vals.update(ov)
        pol = self.env['bca.poliza'].create(vals)
        pol.action_confirmar()
        return pol

    def test_borrador_sin_estatus(self) -> None:
        pol = self.env['bca.poliza'].create({
            'name': 'POL-BORR', 'aseguradora_id': self.aseguradora.id,
            'producto_id': self.producto_vida.id, 'agente_id': self.agente.id,
            'contratante_id': self.env['res.partner'].create({
                'name': 'C Borr', 'bca_tipo': 'contratante'}).id,
            'fecha_inicio': date(2025, 1, 1), 'fecha_fin': date(2027, 1, 1),
            'periodicidad': 'anual', 'prima_anual': 1000.0,
        })
        self.assertFalse(pol.estatus_pago)

    def test_al_corriente_por_corte_reciente(self) -> None:
        reciente = fields.Date.today() - timedelta(days=10)
        pol = self._poliza_activa(pagado_hasta_inicial=reciente)
        self.assertEqual(pol.estatus_pago, 'al_corriente')

    def test_vencido_por_corte_viejo(self) -> None:
        viejo = fields.Date.today() - timedelta(days=120)
        pol = self._poliza_activa(pagado_hasta_inicial=viejo)
        self.assertEqual(pol.estatus_pago, 'vencido')

    def test_suspendido_override(self) -> None:
        pol = self._poliza_activa(pagado_hasta_inicial=fields.Date.today())
        pol.pago_suspendido = True
        self.assertEqual(pol.estatus_pago, 'suspendido')
