from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from odoo.exceptions import UserError, ValidationError
from psycopg2.errors import SerializationFailure


class ParserBase:
    """Clase base de parsers de cobranza (Strategy pattern).

    Las subclases declaran ``aseguradora_codigo``, ``ramo`` y
    ``columnas_requeridas``, e implementan ``_procesar_fila_interna``.

    El wrapper ``procesar_fila`` aplica R-COB-08 (tolerancia a fallos por
    fila): convierte ``ReciboPagadoConcurrenteError`` en ``sin_coincidencia``
    y ``UserError``/``ValidationError`` en ``error``. ``NotImplementedError``
    se propaga para que parsers placeholder (Qualitas) aborten el flujo.
    """

    aseguradora_codigo: str | None = None
    ramo: str | None = None
    columnas_requeridas: list[str] = []

    def __init__(self, env, bitacora) -> None:
        self.env = env
        self.bitacora = bitacora
        self.aseguradora_id: int = bitacora.aseguradora_id.id

    @classmethod
    def validar_estructura(cls, fieldnames: list[str]) -> None:
        """R-COB-09: valida columnas requeridas antes del loop.

        El wizard E8 llama esto con los encabezados del CSV antes de iterar
        (y antes de crear la bitácora), por eso es ``classmethod``: no necesita
        instancia ni bitácora. Lanza ``UserError`` fail-fast — no se crea la
        bitácora si falta una columna crítica. Las llamadas previas sobre
        instancia (``parser.validar_estructura(...)``) siguen funcionando.
        """
        faltantes = [c for c in cls.columnas_requeridas if c not in fieldnames]
        if faltantes:
            raise UserError(
                "El archivo no tiene las columnas requeridas: %s" % faltantes
            )

    def filtrar_filas(self, filas: list[dict]) -> list[tuple[int, dict]]:
        return list(enumerate(filas, start=1))

    def procesar_fila(self, env, fila: dict, numero_fila: int) -> dict:
        """R-COB-08: ejecuta ``_procesar_fila_interna`` aislando errores.

        Retorna ``{'marca','recibo_id','mensaje','numero_poliza_raw'}`` que
        el wizard (E8) usa para crear la línea de bitácora. Las subclases
        sobrescriben ``_procesar_fila_interna``; este wrapper no se toca.

        Import lazy de la excepción tipada: los parsers viven en su propio
        paquete y el modelo bca.recibo los referencia indirectamente vía
        ``_aplicar_lote``; el import al top-level crearía un ciclo de
        importación models ⇄ parsers al registrar el módulo.
        """
        from odoo.addons.BCA_Seguros.models.recibo import ReciboPagadoConcurrenteError

        raw = (fila.get("numero_poliza") or "").strip()
        try:
            return self._procesar_fila_interna(env, fila, numero_fila, raw)
        except NotImplementedError:
            raise
        except ReciboPagadoConcurrenteError as exc:
            return self._linea_sin_coincidencia(raw, str(exc))
        except SerializationFailure:
            # 40001: fallo de transacción (snapshot REPEATABLE READ de este
            # fork), NO de fila. Debe propagarse para que el caller reintente
            # el archivo/lote con una transacción nueva; convertirlo a marca
            # 'error' escondería el fallo de serialización.
            raise
        except (UserError, ValidationError) as exc:
            return self._linea_error(raw, str(exc))
        except Exception as exc:  # noqa: BLE001 — R-COB-08
            return self._linea_error(raw, "Error inesperado: %s" % exc)

    def _procesar_fila_interna(
        self, env, fila: dict, numero_fila: int, raw: str
    ) -> dict:
        raise NotImplementedError

    def _linea_error(self, raw: str, mensaje: str) -> dict:
        return {
            "marca": "error",
            "recibo_id": False,
            "mensaje": mensaje,
            "numero_poliza_raw": raw,
        }

    def _linea_sin_coincidencia(self, raw: str, mensaje: str) -> dict:
        return {
            "marca": "sin_coincidencia",
            "recibo_id": False,
            "mensaje": mensaje,
            "numero_poliza_raw": raw,
        }

    def _buscar_poliza(self, env, raw: str):
        return env["bca.poliza"].search(
            [
                ("name", "=", raw),
                ("aseguradora_id", "=", self.aseguradora_id),
            ],
            limit=1,
        )

    def _resolver_conducto(self, env, valor) -> tuple:
        """Resuelve ``conducto_id`` por ``codigo_archivo``.

        Retorna ``(conducto_id_o_False, advertencia_o_None)``. R-COB-06:
        si el código del CSV no coincide con el catálogo, no aborta — el
        recibo se paga con conducto vacío y el wizard registra advertencia.
        """
        codigo = str(valor or "").strip().upper()
        if not codigo:
            return False, "Columna conducto vacía"
        conducto = env["bca.conducto"].search(
            [
                ("codigo_archivo", "=", codigo),
                ("aseguradora_id", "=", self.aseguradora_id),
                ("activo", "=", True),
            ],
            limit=1,
        )
        if not conducto:
            return False, "Conducto '%s' no encontrado en catálogo" % codigo
        return conducto.id, None

    def normalizar_monto(self, valor) -> float:
        """Convierte ``"1,234.56"``/``"1234.56"`` → ``float`` con 2 decimales.

        Coma se interpreta como separador de miles. Vacío/None → 0.0
        (columnas opcionales como ``recargo`` pueden venir vacías). Valor
        inválido → ``ValidationError``.
        """
        if valor is None:
            return 0.0
        texto = str(valor).strip()
        if not texto:
            return 0.0
        try:
            return float(Decimal(texto.replace(",", "")).quantize(Decimal("0.01")))
        except (InvalidOperation, ValueError) as exc:
            raise ValidationError("Monto inválido: %r" % valor) from exc

    def normalizar_fecha(self, valor) -> date:
        """Convierte ``"DD/MM/YYYY"`` → ``date``."""
        if valor is None:
            raise ValidationError("Fecha vacía")
        texto = str(valor).strip()
        if not texto:
            raise ValidationError("Fecha vacía")
        try:
            return datetime.strptime(texto, "%d/%m/%Y").date()
        except ValueError as exc:
            raise ValidationError("Fecha inválida: %r" % valor) from exc
