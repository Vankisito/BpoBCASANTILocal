from __future__ import annotations

import logging
import threading
import time
import uuid
from contextlib import suppress

from odoo import SUPERUSER_ID, api
from odoo.addons.BCA_Seguros.parsers.metlife_gcaye import (
    COLUMNAS_GCAYE,
    ParserMetLifeGMM,
)
from odoo.addons.BCA_Seguros.parsers.metlife_lsp import COLUMNAS_LSP, ParserMetLifeVida
from odoo.modules.registry import Registry
from odoo.tests.common import BaseCase, get_db_name, tagged
from psycopg2.errors import SerializationFailure

from .test_cobranza_fifo import _CobranzaFixtures

_logger = logging.getLogger(__name__)


class _LockNulo:
    """RLock no-op para Registry._lock mientras corren los workers.

    Los workers se bloqueaban en ``with cls._lock:`` (registry.py:100) porque
    el hilo principal del framework mantiene el lock tomado desde el arranque
    de ``--test-enable`` en este fork. El no-op evita el bloqueo sin tocar el
    estado del lock real (se restaura en ``tearDownClass``).
    """

    def acquire(self, *args, **kwargs) -> bool:
        return True

    def release(self, *args, **kwargs) -> None:
        pass

    def __enter__(self) -> "_LockNulo":
        return self

    def __exit__(self, *args) -> None:
        pass


@tagged("BCA_Seguros")
class TestCobranzaMatchVigencia(_CobranzaFixtures):
    """R-COB-11: match por póliza + vigencia (sin prima).

    Criterios de aceptación del plan:
    1. Doble subida → 1 cobro aplicado + 1 rechazado con motivo.
    2. Vigencia distinta → rechazada con motivo, recibo intacto.
    3. Fila legítima → se aplica con normalidad.
    4. GMM: mismos casos + anulaciones siguen omitiéndose.
    """

    def test_doble_subida_misma_vigencia_no_duplica(self) -> None:
        """Doble subida misma póliza+vigencia → 1 aplicado + 1 sin_coincidencia."""
        pol = self._poliza("PV-DUP")
        filas = [
            self._fila_vida("PV-DUP"),
            self._fila_vida("PV-DUP"),  # segunda vez → sin coincidencia
        ]
        bitacora = self._procesar(COLUMNAS_LSP, filas)

        self.assertEqual(bitacora.recibos_aplicados, 1)
        self.assertEqual(bitacora.recibos_sin_coincidencia, 1)
        marcas = bitacora.linea_ids.mapped("marca")
        self.assertIn("aplicado", marcas)
        self.assertIn("sin_coincidencia", marcas)
        # Solo 1 recibo pagado
        pagados = pol.recibo_ids.filtered(lambda r: r.estado == "pagado")
        self.assertEqual(len(pagados), 1)

    def test_vigencia_distinta_rechazada(self) -> None:
        """Fila con vigencia distinta al recibo → sin_coincidencia, recibo intacto."""
        pol = self._poliza("PV-VIG")
        # La póliza mensual genera recibos con vigencia 01/XX–01/XX+1
        # Enviamos vigencia incorrecta
        filas = [
            self._fila_vida(
                "PV-VIG", vigencia_desde="15/03/2025", vigencia_hasta="15/04/2025"
            ),
        ]
        bitacora = self._procesar(COLUMNAS_LSP, filas)

        self.assertEqual(bitacora.recibos_aplicados, 0)
        self.assertEqual(bitacora.recibos_sin_coincidencia, 1)
        linea = bitacora.linea_ids[0]
        self.assertEqual(linea.marca, "sin_coincidencia")
        self.assertIn("Sin coincidencia", linea.mensaje)
        # Recibo sigue pendiente
        pendientes = pol.recibo_ids.filtered(lambda r: r.estado == "pendiente")
        self.assertTrue(pendientes)

    def test_fila_legitima_se_aplica(self) -> None:
        """Fila con vigencia correcta → se aplica normalmente."""
        pol = self._poliza("PV-OK")
        # Recibo 1 tiene vigencia 01/01/2025–01/02/2025
        filas = [self._fila_vida("PV-OK")]
        bitacora = self._procesar(COLUMNAS_LSP, filas)

        self.assertEqual(bitacora.recibos_aplicados, 1)
        self.assertEqual(bitacora.recibos_sin_coincidencia, 0)
        pagados = pol.recibo_ids.filtered(lambda r: r.estado == "pagado")
        self.assertEqual(len(pagados), 1)
        self.assertEqual(pagados.numero_recibo, 1)

    def test_gmm_doble_subida_no_duplica(self) -> None:
        """GMM: doble subida → 1 aplicado + 1 sin_coincidencia."""
        self._poliza("PG-DUP", ramo="gmm")
        filas = [
            self._fila_gmm("PG-DUP"),
            self._fila_gmm("PG-DUP"),  # segunda vez
        ]
        bitacora = self._procesar(COLUMNAS_GCAYE, filas, ramo="gmm")

        self.assertEqual(bitacora.recibos_aplicados, 1)
        self.assertEqual(bitacora.recibos_sin_coincidencia, 1)

    def test_gmm_anulaciones_siguen_omitiendose(self) -> None:
        """GMM: anulaciones se omiten Y vigencia incorrecta → sin_coincidencia."""
        self._poliza("PG-MIX", ramo="gmm")
        filas = [
            self._fila_gmm("PG-MIX"),
            self._fila_gmm("PG-MIX", estatus_pago="anulado"),
            self._fila_gmm(
                "PG-MIX", vigencia_desde="15/03/2025", vigencia_hasta="15/04/2025"
            ),
        ]
        bitacora = self._procesar(COLUMNAS_GCAYE, filas, ramo="gmm")

        self.assertEqual(bitacora.recibos_aplicados, 1)
        self.assertEqual(bitacora.anulaciones_ignoradas, 1)
        self.assertEqual(bitacora.recibos_sin_coincidencia, 1)

    def test_mensaje_incluye_recibos_pendientes(self) -> None:
        """El mensaje de sin_coincidencia lista los recibos pendientes reales."""
        self._poliza("PV-MSG")
        filas = [
            self._fila_vida(
                "PV-MSG", vigencia_desde="15/03/2025", vigencia_hasta="15/04/2025"
            ),
        ]
        bitacora = self._procesar(COLUMNAS_LSP, filas)

        linea = bitacora.linea_ids[0]
        self.assertEqual(linea.marca, "sin_coincidencia")
        self.assertIn("Recibos pendientes:", linea.mensaje)
        # El mensaje lista recibo.name (REC-XXXXX), no poliza.name
        self.assertIn("REC-", linea.mensaje)
        self.assertIn("2025-01-01", linea.mensaje)  # vigencia del primer recibo


@tagged("BCA_Seguros", "post_install", "-at_install")
class TestCobranzaConcurrencia(BaseCase):
    """Concurrencia real sobre la misma póliza+vigencia.

    Hereda de ``BaseCase`` (NO de TransactionCase) a propósito: TransactionCase
    pone el registry en modo test, y ahí ``registry.cursor()`` devuelve
    ``TestCursor`` — envoltorios sobre UNA MISMA transacción con savepoints y
    un RLock Python compartido. No hay concesión PostgreSQL real y los dos
    "workers" se bloquean el ''registro'' entre ellos (hang).

    Con ``BaseCase``, ``registry.cursor()`` devuelve cursores reales: 2
    conexiones/transacciones PostgreSQL independientes con commit real. El lock
    ``FOR UPDATE`` de ``_aplicar_lote`` se ejercita de verdad.

    Los fixtures se crean commiteando (los ven ambas conexiones) y se borran
    SIEMPRE en ``finally`` (claves únicas por corrida).
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # BaseCase no setea registry; sin modo test → cursores reales.
        cls.registry = Registry(get_db_name())
        # Este fork deja Registry._lock tomado por el hilo principal desde el
        # arranque de ``--test-enable`` (un acquire sin liberar del framework).
        # RLock es reentrante → el main no nota nada; los hilos worker sí quedan
        # bloqueados en Registry.__new__ (registry.py:100). En lugar de liberar
        # (rompería el ``with Registry._lock`` del shutdown), lo neutralizamos
        # con un no-op durante la corrida y lo restauramos en tearDownClass.
        cls._registry_lock_original = Registry._lock
        Registry._lock = _LockNulo()
        _logger.info(
            "Concurrencia: Registry._lock neutralizado "
            "(leak de arranque del framework)"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        Registry._lock = cls._registry_lock_original
        super().tearDownClass()

    def test_dos_importaciones_vida_misma_vigencia_aplica_una_sola_vez(
        self,
    ) -> None:
        """Vida mensual: 2 tx concurrentes misma vigencia → 1 aplicado + 1
        sin_coincidencia y exactamente 1 recibo pagado."""
        fixtures = self._fixture_commiteada(ramo="vida", periodicidad="mensual")
        try:
            fila = self._fila_vida_con_fixture(fixtures)
            resultados = self._ejecutar_race(fila, ParserMetLifeVida, "vida", fixtures)
            self._assert_unico_pago(fixtures, resultados)
        finally:
            self._limpiar_fixtures_commiteadas(fixtures)

    def test_dos_importaciones_gmm_misma_vigencia_aplica_una_sola_vez(
        self,
    ) -> None:
        """GMM: mismo escenario que Vida → 1 aplicado + 1 sin_coincidencia."""
        fixtures = self._fixture_commiteada(ramo="gmm", periodicidad="mensual")
        try:
            fila = self._fila_gmm_con_fixture(fixtures)
            resultados = self._ejecutar_race(fila, ParserMetLifeGMM, "gmm", fixtures)
            self._assert_unico_pago(fixtures, resultados)
        finally:
            self._limpiar_fixtures_commiteadas(fixtures)

    def test_anualidad_se_genera_una_sola_vez_bajo_concurrencia(self) -> None:
        """Anual: 2 tx concurrentes pagan el único recibo → 1 sola anualidad
        generada. El perdedor (lock de R1) puede ver la anualidad nueva
        (sin_coincidencia) o nada (sin_recibo) según el snapshot — ambas
        válidas; lo que NO puede pasar es pagar 2 veces o crear 2 anualidades.
        """
        fixtures = self._fixture_commiteada(ramo="vida", periodicidad="anual")
        try:
            fila = self._fila_vida_con_fixture(
                fixtures,
                vigencia_desde="01/01/2025",
                vigencia_hasta="01/01/2026",
                prima_total="12,000.00",
            )
            resultados = self._ejecutar_race(fila, ParserMetLifeVida, "vida", fixtures)
            self.assertIn(
                "aplicado",
                resultados,
                "debe haber exactamente 1 aplicado: %s" % resultados,
            )
            otros = [r for r in resultados if r != "aplicado"]
            self.assertEqual(
                len(otros), 1, "debe haber 1 solo aplicado: %s" % resultados
            )
            self.assertIn(
                otros[0],
                ("sin_coincidencia", "sin_recibo"),
                "perdedor debe ser sin_coincidencia/sin_recibo: %s" % resultados,
            )
            with self.registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                recibos = (
                    env["bca.recibo"]
                    .sudo()
                    .search(
                        [
                            ("poliza_id", "=", fixtures["poliza_id"]),
                        ]
                    )
                )
                # R1 pagado + 1 única anualidad siguiente
                self.assertEqual(
                    len(recibos), 2, "debe haber 2 recibos (R1 + anualidad)"
                )
                pagados = recibos.filtered(lambda r: r.estado == "pagado")
                self.assertEqual(len(pagados), 1, "solo 1 recibido pagado")
        finally:
            self._limpiar_fixtures_commiteadas(fixtures)

    # -- helpers -------------------------------------------------------- #
    def _fila_vida(self, poliza_name: str, **ov) -> dict:
        fila = {
            "numero_poliza": poliza_name,
            "producto": "TempoLife Cobranza",
            "agente": "C100",
            "contratante": "Contratante C",
            "moneda": "MXN",
            "fecha_aplicacion": "15/01/2025",
            "vigencia_desde": "01/01/2025",
            "vigencia_hasta": "01/02/2025",
            "conducto": "",
            "prima_modal": "1,000.00",
            "recargo": "0.00",
            "prima_total_pagada": "1,000.00",
        }
        fila.update(ov)
        return fila

    def _fila_gmm(self, poliza_name: str, **ov) -> dict:
        fila = {
            "numero_poliza": poliza_name,
            "estatus_pago": "vigente",
            "agente": "C100",
            "contratante": "Contratante C",
            "fecha_aplicacion": "15/01/2025",
            "vigencia_desde": "01/01/2025",
            "vigencia_hasta": "01/02/2025",
            "conducto": "",
            "prima_neta": "1,000.00",
            "recargo": "0.00",
            "gastos_expedicion": "0.00",
            "impuestos": "0.00",
            "prima_total_pagada": "1,000.00",
        }
        fila.update(ov)
        return fila

    def _fixture_commiteada(self, ramo: str, periodicidad: str) -> dict:
        """Crea póliza+recibos en una transacción real y la commitea, para
        que las 2 conexiones de workers la vean. Claves únicas por corrida."""
        tag = uuid.uuid4().hex[:6].upper()
        nombre_poliza = "CONC-%s-%s-%s" % (ramo, periodicidad, tag)
        clave_agente = "CONC-%s-AG" % tag
        codigo_cond = "CONC-%s-C" % tag
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            aseguradora = env.ref("BCA_Seguros.partner_metlife")
            holding = env["res.partner"].create(
                {
                    "name": "Holding %s" % tag,
                    "bca_tipo": "holding",
                }
            )
            promotoria = env["res.partner"].create(
                {
                    "name": "Promotoria %s" % tag,
                    "bca_tipo": "promotoria",
                    "parent_id": holding.id,
                }
            )
            agente = env["res.partner"].create(
                {
                    "name": "Agente %s" % tag,
                    "bca_tipo": "agente",
                    "parent_id": promotoria.id,
                }
            )
            env["res.partner.agente.aseguradora"].create(
                {
                    "agente_id": agente.id,
                    "aseguradora_id": aseguradora.id,
                    "clave_agente": clave_agente,
                    "estado": "clave_definitiva",
                }
            )
            contratante = env["res.partner"].create(
                {
                    "name": "Contratante %s" % tag,
                }
            )
            producto = env["product.template"].create(
                {
                    "name": "Prod %s" % tag,
                    "bca_es_producto_seguro": True,
                    "bca_aseguradora_id": aseguradora.id,
                    "bca_ramo": ramo,
                }
            )
            conducto = env["bca.conducto"].create(
                {
                    "name": "Conducto %s" % tag,
                    "codigo_archivo": codigo_cond,
                    "aseguradora_id": aseguradora.id,
                }
            )
            poliza = env["bca.poliza"].create(
                {
                    "name": nombre_poliza,
                    "aseguradora_id": aseguradora.id,
                    "producto_id": producto.id,
                    "agente_id": agente.id,
                    "contratante_id": contratante.id,
                    "periodicidad": periodicidad,
                    "fecha_inicio": "2025-01-01",
                    "fecha_fin": "2027-01-01",
                    "prima_anual": 12000.0,
                }
            )
            poliza.action_confirmar()
            cr.commit()
            return {
                "poliza_id": poliza.id,
                "poliza_name": nombre_poliza,
                "aseguradora_id": aseguradora.id,
                "holding_id": holding.id,
                "promotoria_id": promotoria.id,
                "agente_id": agente.id,
                "contratante_id": contratante.id,
                "producto_id": producto.id,
                "conducto_id": conducto.id,
                "clave_agente": clave_agente,
                "codigo_cond": codigo_cond,
            }

    def _fila_vida_con_fixture(self, fixtures: dict, **ov) -> dict:
        fila = self._fila_vida(fixtures["poliza_name"])
        fila["conducto"] = fixtures["codigo_cond"]
        fila.update(ov)
        return fila

    def _fila_gmm_con_fixture(self, fixtures: dict, **ov) -> dict:
        fila = self._fila_gmm(fixtures["poliza_name"])
        fila["conducto"] = fixtures["codigo_cond"]
        fila.update(ov)
        return fila

    def _ejecutar_race(self, fila: dict, parser_cls, ramo: str, fixtures: dict) -> list:
        """Lanza 2 workers con conexiones reales propias sobre la misma fila.
        El gate permite que ambos pisen el lock casi a la vez. Devuelve los
        resultados (marca o excepción) de cada worker."""
        gate = threading.Event()
        resultados = []
        workers = [
            threading.Thread(
                target=self._worker,
                args=(fila, parser_cls, ramo, fixtures, gate, resultados, i),
            )
            for i in (1, 2)
        ]
        for w in workers:
            w.start()
        time.sleep(0.3)  # ambos en el gate simultáneamente
        gate.set()
        for w in workers:
            w.join(timeout=30)
            self.assertFalse(w.is_alive(), "worker colgado (deadlock de lock)")
        return resultados

    def _worker(
        self,
        fila: dict,
        parser_cls,
        ramo: str,
        fixtures: dict,
        gate: threading.Event,
        resultados: list,
        n: int,
    ) -> None:
        try:
            gate.wait(timeout=30)
            marca, mensaje = self._importar_una_vez(fila, parser_cls, ramo, fixtures, n)
        except SerializationFailure:
            # Este fork corre REPEATABLE READ (sql_db.py: en Cursor.__init__
            # set_isolation_level(REPEATABLE_READ)). El primer intento del
            # perdedor aborta con 40001 en el propio ``SELECT FOR UPDATE`` de
            # _aplicar_lote (el predicado estado='pendiente' no encuentra la
            # versión ya commiteada del recibo pagado). Reintento con una
            # transacción nueva → snapshot fresco → ve el recibo pagado y
            # devuelve sin_recibo/sin_coincidencia.
            _logger.info("Concurrencia worker%d: retry por serialization", n)
            marca, mensaje = self._importar_una_vez(fila, parser_cls, ramo, fixtures, n)
        except Exception as exc:  # noqa: BLE001 — registra fallos del worker
            _logger.error("Concurrencia worker%d error: %r", n, exc, exc_info=True)
            resultados.append("EXC:%s" % exc)
            return
        resultados.append(marca)
        _logger.info("Concurrencia worker%d: marca=%s mensaje=%s", n, marca, mensaje)

    def _importar_una_vez(
        self, fila: dict, parser_cls, ramo: str, fixtures: dict, n: int
    ) -> tuple:
        """Intento único con transacción/cursor frescos.

        ``procesar_fila`` re-propaga ``SerializationFailure`` (parser/base);
        el resto de excepciones de negocio ya quedan mapeadas a marcas dentro
        del wrapper."""
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            # name explícito: el default usa ir.sequence (fila compartida);
            # bajo REPEATABLE READ 2 workers → 40001 en commit por la fila de
            # la secuencia. Con name propio, la única fila compartida de la
            # race es el recibo (guardada por el FOR UPDATE de _aplicar_lote).
            bitacora = env["bca.bitacora.importacion"].create(
                {
                    "aseguradora_id": fixtures["aseguradora_id"],
                    "ramo": ramo,
                    "nombre_archivo": "concurrente_%d.csv" % n,
                    "name": "conc_%s_%d" % (fila.get("numero_poliza", "x")[:20], n),
                }
            )
            parser = parser_cls(env, bitacora)
            res = parser.procesar_fila(env, fila, 1)
            cr.commit()
            return res["marca"], res["mensaje"]

    def _assert_unico_pago(self, fixtures: dict, resultados: list) -> None:
        """1 aplicado; el perdedor ve el recibo ya pagado (sin_recibo) o no
        encuentra vigencia (sin_coincidencia) según el snapshot post-lock."""
        self.assertIn(
            "aplicado", resultados, "debe haber exactamente 1 aplicado: %s" % resultados
        )
        otros = [r for r in resultados if r != "aplicado"]
        self.assertEqual(len(otros), 1, "debe haber 1 solo aplicado: %s" % resultados)
        self.assertIn(
            otros[0],
            ("sin_coincidencia", "sin_recibo"),
            "perdedor debe ser sin_coincidencia/sin_recibo: %s" % resultados,
        )
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            pagados = (
                env["bca.recibo"]
                .sudo()
                .search(
                    [
                        ("poliza_id", "=", fixtures["poliza_id"]),
                        ("estado", "=", "pagado"),
                    ]
                )
            )
            self.assertEqual(len(pagados), 1, "solo 1 recibo pagado")

    def _limpiar_fixtures_commiteadas(self, fixtures: dict) -> None:
        """Borra los fixtures propios (ya commiteados) para dejar la BD local
        sin residuos. Usa claves únicas del fixture, no constantes."""
        with suppress(Exception):  # noqa: SIM117, BLE001 — limpieza nunca rompe el test
            with self.registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                env["bca.bitacora.importacion"].sudo().search(
                    [
                        ("aseguradora_id", "=", fixtures["aseguradora_id"]),
                        ("nombre_archivo", "like", "concurrente_%"),
                    ]
                ).unlink()
                env["bca.recibo"].sudo().search(
                    [
                        ("poliza_id", "=", fixtures["poliza_id"]),
                    ]
                ).unlink()
                poliza = env["bca.poliza"].sudo().browse(fixtures["poliza_id"])
                if poliza.exists():
                    poliza.unlink()
                env["res.partner.agente.aseguradora"].sudo().search(
                    [
                        ("clave_agente", "=", fixtures["clave_agente"]),
                    ]
                ).unlink()
                env["res.partner"].sudo().browse(
                    [
                        fixtures["holding_id"],
                        fixtures["promotoria_id"],
                        fixtures["agente_id"],
                        fixtures["contratante_id"],
                    ]
                ).unlink()
                env["product.template"].sudo().browse(fixtures["producto_id"]).unlink()
                conducto = env["bca.conducto"].sudo().browse(fixtures["conducto_id"])
                if conducto.exists():
                    conducto.unlink()
                cr.commit()
