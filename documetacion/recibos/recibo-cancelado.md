# Recibo cancelado

Un recibo en estado **Cancelado** fue anulado y no se cobrará.

## Cuándo y cómo se cancela

- La cancelación de un recibo se hace con la acción **Anular recibo**.
- Solo aplica a recibos en estado **Pendiente**.
- Requiere rol autorizado (Director / Director Comercial).

## Efectos

- El recibo queda en estado **Cancelado** y se conserva como histórico (no se borra).
- **No** se registra cobranza ni PCA para ese recibo.
- El recibo deja de ser cobrable.

## Diferencia: Cancelado vs Cancelar pago

| Concepto | Acción | Resultado |
|---|---|---|
| **Anular recibo** | Recibo pendiente → Cancelado | No se cobrará nunca. |
| **Cancelar pago** | Recibo pagado → Pendiente | Se revierte un pago ya registrado. |

> No confundir ambas operaciones. **Anular** descarta un recibo pendiente; **cancelar el pago** deshace una cobranza hecha.

## Notas

- Un recibo cancelado permanece en la lista de recibos de la póliza para auditoría.
- La cancelación de un recibo es distinta de la **cancelación de la póliza** (ver *polizas/cancelar-poliza*).
