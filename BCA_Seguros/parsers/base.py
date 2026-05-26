class ParserBase:
    aseguradora_codigo = None
    ramo = None
    columnas_requeridas = []

    def __init__(self, env, bitacora):
        self.env = env
        self.bitacora = bitacora

    def validar_estructura(self, df):
        """Verifica que el DataFrame tenga todas las columnas requeridas."""
        faltantes = [c for c in self.columnas_requeridas if c not in df.columns]
        if faltantes:
            from odoo.exceptions import UserError
            raise UserError(
                f"El archivo no tiene las columnas requeridas: {faltantes}"
            )

    def filtrar_filas(self, df):
        return df

    def procesar_fila(self, env, fila):
        raise NotImplementedError

    def normalizar_monto(self, valor):
        raise NotImplementedError

    def normalizar_fecha(self, valor):
        raise NotImplementedError
