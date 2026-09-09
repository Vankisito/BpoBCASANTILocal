# Flujo general de cobranza

El proceso de cobranza recorre los siguientes pasos, desde que llega el archivo hasta que el recibo queda pagado.

## Paso a paso (cobranza por archivo)

```text
1. La aseguradora entrega el archivo de cobranza (CSV).
        │
2. Se descarga la plantilla correcta y se prepara el archivo
   con el formato esperado.  (descargar-plantilla · preparar-csv)
        │
3. Se abre el asistente de Cobranza Diaria y se sube el archivo.
        │
4. Se indican la Aseguradora y el Ramo (vida/gmm).
        │
5. Se valida la estructura del archivo (columnas requeridas).
        │
6. Se procesan las filas, una por una, con aislamiento de errores.
   - Se localiza la póliza.
   - Se identifica el recibo pendiente (FIFO).
   - Se aplica el pago → recibo Pagado → PCA congelada.
        │
7. Se genera la bitácora de importación con totales.
        │
8. Se abre la bitácora para revisar el resultado.
```

## Qué ocurre por fila

Cada fila del archivo produce un resultado:

- **Aplicado**: el pago se registró correctamente.
- **Advertencia**: pago aplicado pero con aviso (p. ej. conducto sin coincidencia).
- **Póliza no encontrada**: el número de póliza no existe en el sistema.
- **Sin recibo pendiente**: la póliza no tiene recibo por cobrar.
- **Error**: problema al procesar la fila.

## Cobranza manual

Alternativa sin archivo: desde el recibo pendiente, **Registrar Pago** (ver *registrar-pago-manual*).

## Notas

- La cobranza por archivo mantiene un **rollback aislado por fila**: el error de una fila no detiene las demás.
- Al final, la bitácora resume filas totales, pagos aplicados, no encontradas y errores.
