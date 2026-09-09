# Estados del recibo

Estos son los estados exactos de un recibo y las transiciones permitidas.

## Estados

| Estado | Significado |
|---|---|
| **Pendiente** | Recibo por cobrar dentro del plan de pagos. |
| **Pagado** | Cobranza registrada; PCA congelada. |
| **Cancelado** | Recibo anulado; no se cobrará. |

## Transiciones permitidas

```text
Pendiente ──Registrar pago──> Pagado
Pendiente ──Anular recibo──> Cancelado
Pagado    ──Cancelar pago──> Pendiente  (revierte el pago)
```

## Detalle de cada transición

| Transición | Acción | Efecto |
|---|---|---|
| Pendiente → Pagado | **Registrar pago** (manual o por archivo) | Se calcula y congela la PCA; se actualiza Pagado Hasta. |
| Pendiente → Cancelado | **Anular recibo** | El recibo no se cobra; permanece como histórico cancelado. |
| Pagado → Pendiente | **Cancelar pago** (solo roles autorizados) | Se limpia la PCA y el pago; el recibo vuelve a pendiente. |

## Reglas

- **FIFO**: los recibos se pagan en orden de `numero_recibo`; no se puede pagar uno si hay un pendiente anterior (ver *regla-fifo*).
- **Cancelar pago** requiere rol autorizado (Director / Director Comercial).
- **Anular recibo** solo aplica a recibos pendientes.
