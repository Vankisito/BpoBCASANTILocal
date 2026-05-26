from .base import CalculadorPCABase


class CalculadorPCAMetLife(CalculadorPCABase):
    aseguradora_codigo = 'METLIFE'

    def calcular(self, recibo):
        """Retorna (pca, factor_aplicado, motivo_exclusion). Implementar en Etapa 7."""
        raise NotImplementedError
