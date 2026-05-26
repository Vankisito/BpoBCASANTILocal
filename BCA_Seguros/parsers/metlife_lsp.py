from .base import ParserBase


class ParserMetLifeVida(ParserBase):
    aseguradora_codigo = 'METLIFE'
    ramo = 'vida'
    columnas_requeridas = []  # Implementar en Etapa 6 con los 13 campos del archivo LSP

    def procesar_fila(self, env, fila):
        raise NotImplementedError

    def normalizar_monto(self, valor):
        raise NotImplementedError

    def normalizar_fecha(self, valor):
        raise NotImplementedError
