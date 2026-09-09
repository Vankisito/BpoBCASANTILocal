# Filtros y agrupaciones

Los reportes del área permiten filtrar y agrupar la información por distintas dimensiones.

## Filtros comunes

| Filtro | Dónde se aplica |
|---|---|
| **Fecha de pago** | PCA y cobranza. |
| **Aseguradora** | PCA, cartera, cobranza. |
| **Ramo** | PCA, cartera. |
| **Agente** | PCA, recibos, cobranza. |
| **Promotoría** | PCA, recibos, cartera. |
| **Estado** | Recibos (pendiente/pagado/cancelado), pólizas. |

## Agrupaciones

- **PCA por agente**: agrupa por agente, aseguradora, ramo, producto, fecha.
- **PCA por promotoría**: agrupa por promotoría, aseguradora, ramo.
- **PCA consolidada**: drill-down holding → promotoría → agente → ramo.
- **Reporte de recibos**: agrupa por estado, agente, promotoría, póliza.

## Formato de vistas

- Las vistas **pivot** (por defecto en los reportes de PCA) permiten arrastrar dimensiones.
- Se complementan con vistas de **gráfica** y **lista**.

## Reglas de negocio aplicadas

- Los reportes de PCA solo muestran pagos con el agente en **Clave Definitiva** en la aseguradora.
- Usan la **foto inmutable** del recibo (no la póliza actual).

## Notas

- Los filtros de PCA por fechas se aplican a la **fecha de pago**.
- Cada reporte indica sus dimensiones y métricas disponibles.
