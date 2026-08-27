# Reporte de cobranza

El reporte de **cobranza** muestra la información de los pagos registrados.

## Qué muestra

- Recibos en estados relevantes para la cobranza (pendientes, pagados).
- Montos cobrados por periodo.
- Filtros por aseguradora, ramo, póliza, agente, fecha de pago.

## Filtros principales

| Filtro | Uso |
|---|---|
| Fecha de pago / periodo | Rango de fechas de cobro. |
| Aseguradora | Limita a una aseguradora. |
| Ramo | Limita a un ramo. |
| Agente / promotoría | Producción por red. |
| Estado | Pendiente / pagado / cancelado. |

## Origen de los datos

- Se alimenta de los **recibos** y sus pagos.
- Complementa la visión del tablero (montos cobrados del mes, próximos cobros).

## Uso

- Conciliar cobranza por periodo.
- Seguimiento de pendientes y morosidad.

## Notas

- La **bitácora** de importación registra el detalle auditable de cada corrida (ver cobranza → *bitacora-cobranza*).
- El reporte de cobranza se distingue de la bitácora: muestra los recibos, la bitácora audita la carga.
