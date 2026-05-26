from .base import ParserBase


class ParserMetLifeGMM(ParserBase):
    aseguradora_codigo = 'METLIFE'
    ramo = 'gmm'
    columnas_requeridas = []  # Implementar en Etapa 6 con los campos del archivo GCAYE

    def procesar_fila(self, env, fila):
        raise NotImplementedError

    def normalizar_monto(self, valor):
        raise NotImplementedError

    def normalizar_fecha(self, valor):
        raise NotImplementedError
