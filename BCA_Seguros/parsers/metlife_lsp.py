from __future__ import annotations

from .base import ParserBase

# TODO Etapa 8: confirmar nombres exactos de columnas contra un CSV real
# de MetLife (archivo LSP — ramo Vida). Los nombres aquí son tentativos
# según specs §5.3 (Lógica de Negocios) y §4.2 (Arquitectura). Pueden
# requerir ajuste por acentos, mayúsculas o espacios del CSV real.
COLUMNAS_LSP = [
    "numero_poliza",
    "producto",
    "agente",
    "contratante",
    "moneda",
    "fecha_aplicacion",
    "vigencia_desde",
    "vigencia_hasta",
    "conducto",
    "prima_modal",
    "recargo",
    "prima_total",
    "comision_informativa",
]


class ParserMetLifeVida(ParserBase):
    """Parser del archivo LSP de MetLife (ramo Vida).

    Reglas aplicadas: R-COB-02 (póliza no encontrada), R-COB-03 (FIFO,
    delegado a ``action_registrar_pago``), R-COB-04 (sin recibo pendiente),
    R-COB-06 (conducto sin match → advertencia, no aborta), R-COB-08
    (tolerancia por fila vía wrapper de base), R-GLOB-01 (encoding Latin-1
    gestionado por el wizard E8 antes de invocar este parser).

    El pago y match son atómicos vía ``bca.recibo._aplicar_lote`` que
    bloquea pendientes de la póliza, matchea por vigencia y paga en una
    sola sección transaccional.
    """

    aseguradora_codigo = "METLIFE"
    ramo = "vida"
    columnas_requeridas = COLUMNAS_LSP

    def _procesar_fila_interna(
        self, env, fila: dict, numero_fila: int, raw: str
    ) -> dict:
        poliza = self._buscar_poliza(env, raw)
        if not poliza:
            return {
                "marca": "no_encontrada",
                "recibo_id": False,
                "mensaje": "Póliza no existe en el sistema",
                "numero_poliza_raw": raw,
            }

        vigencia_desde = self.normalizar_fecha(fila.get("vigencia_desde"))
        vigencia_hasta = self.normalizar_fecha(fila.get("vigencia_hasta"))
        fecha_pago = self.normalizar_fecha(fila.get("fecha_aplicacion"))
        prima_neta = self.normalizar_monto(fila.get("prima_modal"))
        recargo = self.normalizar_monto(fila.get("recargo"))
        prima_total = self.normalizar_monto(fila.get("prima_total"))
        conducto_id, advertencia = self._resolver_conducto(env, fila.get("conducto"))

        vals = {
            "fecha_pago": fecha_pago,
            "prima_total_pagada": prima_total or prima_neta,
            "recargo": recargo,
            "conducto_id": conducto_id,
            "folio_endoso": False,
        }

        resultado = env["bca.recibo"]._aplicar_lote(
            poliza.id,
            vigencia_desde,
            vigencia_hasta,
            vals,
        )
        resultado["numero_poliza_raw"] = raw

        if advertencia and resultado["marca"] == "aplicado":
            resultado["mensaje"] += " | %s" % advertencia
            resultado["marca"] = "advertencia"

        return resultado
