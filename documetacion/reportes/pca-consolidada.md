# PCA consolidada

El reporte de **PCA Consolidada** muestra la producción a nivel de **holding / BCA**, con capacidad de profundizar.

## Cómo consultarlo

- Menú **Reportes** → **PCA Consolidada** del área Gestión de Seguros.

## Qué muestra

- Grano fino: un **recibo pagado** por fila, para permitir el drill-down.
- Jerarquía: **promotoría → agente → aseguradora → ramo**.
- Métricas: **PCA** (en MXN) por recibo.

## Regla de filtrado

- Misma base que los reportes anteriores: recibos **pagados** con agente en **Clave Definitiva** en la aseguradora.
- Usa la foto inmutable del recibo.

## Uso

- Ver el **total consolidado** de producción de BCA.
- Profundizar (drill-down) desde el holding hasta promotoría → agente → ramo → recibo.
- Base para la **liquidación** a la red (comisiones).

## Formato

- Pivot con desglose jerárquico (holding → promotoría → agente).
- Filtra por promotoría, agente, aseguradora, ramo, fecha de pago.

## Notas

- Al conservar filas detalladas, el "consolidado" es el total que el pivot agrega manteniendo la capacidad de abrir hacia abajo.
