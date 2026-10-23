# Pagos aplicados

Los **pagos aplicados** son los recibos que sí pudieron cobrarse correctamente durante una corrida de cobranza.

## Cómo se ven

- En la **bitácora de importación** se reporta el contador **Recibos Aplicados**.
- El detalle por línea de la bitácora marca cada fila como **aplicado**.
- En el recibo, el estado pasa a **Pagado**.

## Qué significa un pago aplicado

- Se localizó la póliza.
- Se identificó el recibo pendiente correcto (FIFO).
- Se aplicó el pago con su fecha de pago.
- Se congeló la **PCA** y se actualizó el **Pagado Hasta**.

## Consulta

1. Abre la **bitácora** de la corrida (ver *bitacora-cobranza*).
2. Revisa el total de **Recibos Aplicados**.
3. Abre cada línea "aplicado" para ver el recibo resultante.

## Marcas de pago

En la bitácora, además de `aplicado`, existen:

- `advertencia`: pago aplicado pero con aviso (p. ej. conducto sin coincidencia).
- `error` / `no_encontrada` / `sin_recibo`: no se aplicó.

> Un pago con marca `advertencia` **sí cuenta** como aplicado, solo que incluye una nota a revisar.
