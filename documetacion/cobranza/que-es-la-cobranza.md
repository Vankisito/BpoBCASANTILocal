# ¿Qué es la cobranza?

La **cobranza** es el proceso mediante el cual se registran los **pagos** de los recibos de las pólizas, conciliando la información que llega de las aseguradoras con los recibos del sistema.

## Qué resuelve

- Registrar y conciliar los **pagos de prima** recibidos.
- Marcar los recibos como **Pagado** en el orden correcto (FIFO).
- Dejar una **bitácora auditable** de cada carga/importación.
- Alimentar el **Pagado Hasta** de las pólizas y la **PCA** de los pagos.

## Formas de cobranza

| Forma | Descripción |
|---|---|
| **Por archivo (CSV)** | Importar el archivo de cobranza diaria que envía la aseguradora. |
| **Manual** | Registrar un pago directo sobre un recibo pendiente. |

## Concepto

```text
Archivo/CSV o pago manual
   └─> Se localiza la póliza
        └─> Se identifica el recibo pendiente (FIFO)
             └─> Se aplica el pago → recibo Pagado
                  └─> Se congela PCA y se actualiza Pagado Hasta
```

## Notas

- Cada carrera de cobranza por archivo genera una **bitácora** de auditoría (ver *bitacora-cobranza*).
- El proceso respeta la **regla FIFO**: siempre se paga primero el recibo pendiente más antiguo.
- Los pagos pueden venir marcados como aplicados, errores, pólizas no encontradas o advertencias (ver *errores-procesamiento*).
