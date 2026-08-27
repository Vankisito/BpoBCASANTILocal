# Interpretar los indicadores

Este documento explica qué significa cada indicador clave del tablero y los reportes.

## Cartera

| Indicador | Significado |
|---|---|
| Pólizas activas | Pólizas en estado Activa (vigentes, con plan de pagos). |
| En borrador | Pólizas aún sin confirmar. |
| Vencidas / expiradas | Pólizas cuyo plazo terminó. |
| Al día / por caer / sin cobertura | Salud de pago según Pagado Hasta y período de gracia. |

## Cobranza

| Indicador | Significado |
|---|---|
| Cobrado del mes | Suma de pagos del mes. |
| Próximos cobros | Recibos pendientes (FIFO) por cobrar. |
| Pendientes / vencidos | Recibos por pagar y pólizas con pago vencido. |

## Agentes

| Indicador | Significado |
|---|---|
| Con licencia | Agentes con Clave Definitiva. |
| Prospectos | Agentes sin clave (Prospecto). |
| PCA por promotoría | Producción acreditada por cada promotoría. |

## PCA

| Indicador | Significado |
|---|---|
| PCA por agente | Producción acreditada a cada agente (MXN). |
| PCA consolidada | Total de producción de BCA. |
| Factor aplicado | Tasa usada para cada pago. |
| PCA en 0 | Pago sin producción (exclusión o sin factor). |

## Cómo leer un reporte de PCA

```text
Recibo pagado
   + producto no excluido
   + factor vigente
   + agente en Clave Definitiva
      ==> aparece con su PCA en MXN
```

## Notas

- La PCA se expresa siempre en **MXN**.
- Los montos del tablero/reportes respetan los **permisos** de cada rol.
- Si un indicador no coincide con lo esperado, revisa los filtros y la sección PCA → *pca-en-cero* y *cuando-cuenta*.
