# Procesamiento por ramo

La cobranza distingue el procesamiento según el **ramo** del archivo.

## Ramos disponibles en cobranza

| Ramo | Uso |
|---|---|
| **Vida** | Layout de cobranza del ramo Vida. |
| **GMM** | Layout de cobranza del ramo GMM (Gastos Médicos Mayores). |

> Autos (placeholder) queda actualmente fuera del selector.

## Diferencias de procesamiento

- **Vida (LSP)**: usa el parser de Vida, con sus columnas requeridas y su lógica.
- **GMM (GCAYE)**: usa el parser GMM, que además **omite los registros anulados** en el filtrado de filas.
- Cada ramo define sus **columnas requeridas** y el formato esperado.

## Implicaciones

- El ramo elegido **debe coincidir** con el contenido del archivo; de lo contrario el procesamiento no será correcto.
- La búsqueda de la póliza y la aplicación del pago dependen del ramo seleccionado.
- El cálculo de **PCA** varía según el ramo (ver sección PCA → *pca-por-ramo*).

## Notas

- En GMM se ignoran las **anulaciones** que vienen en el archivo.
- Usa siempre la plantilla y el ramo correctos para la corrida.
