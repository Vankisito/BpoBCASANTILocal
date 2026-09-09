# Reporte de recibos

El reporte de **recibos** lista los recibos de todas las pólizas con su estado e importes.

## Qué muestra

- Número de recibo, póliza, periodo (desde/hasta).
- Importes (prima neta, total).
- Estado (pendiente, pagado, cancelado).
- Fecha de pago y conducto.
- Agente / promotoría (asociados al recibo).

## Filtros

- Por estado, póliza, aseguradora, ramo, agente, fecha de pago, periodo de cobertura.

## Agrupaciones útiles

- Por agente: para ver la cartera de cada agente.
- Por estado: pendientes vs pagados vs cancelados.
- Por promotoría: cartera de cada promotoría.

## Origen de los datos

- Modelo `bca.recibo` (recibos del sistema).

## Uso

- Monitorear la cobranza a nivel de recibo.
- Identificar pendientes y recibos cancelados.

## Notas

- Los recibos **pagados** conservan la PCA congelada (ver sección PCA).
- Los recibos se generan del plan de pagos, no se crean a mano.
