# Importar cobranza diaria

La cobranza por archivo se importa desde el asistente **Cobranza Diaria**.

## Pasos

1. Abre el asistente **Cobranza Diaria** (área Gestión de Seguros).
2. Selecciona la **Aseguradora** (default: MetLife).
3. Selecciona el **Ramo**: Vida o GMM.
4. Adjunta el archivo **CSV** en el campo *Archivo de Cobranza*.
5. Pulsa **Procesar**.

> El campo de archivo no es estrictamente obligatorio en pantalla para permitir descargar la plantilla; la obligatoriedad real se valida al procesar.

## Qué ocurre al procesar

1. Se valida la **estructura** del archivo (columnas requeridas).
2. Se crea la **bitácora** de importación.
3. Se procesan las filas, aplicando pagos en **FIFO** y aislando errores por fila.
4. Se calculan totales (aplicados, no encontrados, errores, PCA de la sesión).
5. Se abre la **bitácora** resultante para revisión.

## Correcto

- Si todo sale bien, los recibos quedan **Pagado** y la PCA congelada.
- La bitácora resume el resultado de la corrida.

## Problemas

- Si el archivo no tiene las columnas requeridas, se rechaza **antes** de crear la bitácora.
- Las pólizas no encontradas o errores por fila se reportan en la bitácora sin detener el resto (ver *errores-procesamiento*).
