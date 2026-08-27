# Procesamiento por aseguradora

La cobranza distingue el procesamiento según la **aseguradora** emisora del archivo.

## Cómo se decide

- En el asistente se elige la **Aseguradora** de la corrida.
- El sistema selecciona el **parser** correspondiente según el **código de aseguradora** (p. ej. METLIFE).
- Cada parser define sus **columnas requeridas** y su lógica de parseo.

## Aseguradoras con parser real

- **MetLife** incluye parsers para sus layouts de cobranza:
  - **LSP** → ramo **Vida**.
  - **GCAYE** → ramo **GMM**.

## Aseguradoras placeholder

- Otras aseguradoras (p. ej. Qualitas) se mantienen como **placeholder** y quedan **fuera del selector** de cobranza hasta que se implemente su parser.

## Implicaciones

- Al importar, debes elegir la aseguradora correcta para que el archivo se procese con el parser adecuado.
- La búsqueda de pólizas se restringe a las de esa aseguradora.
- El cálculo de **PCA** usa el calculador correspondiente a la aseguradora de la póliza.

## Notas

- La aseguradora debe tener configurado su **código** (`bca_codigo_aseguradora`); sin él, el proceso no avanza.
- El selector de cobranza actualmente ofrece los ramos Vida y GMM (con parser real) para MetLife.
