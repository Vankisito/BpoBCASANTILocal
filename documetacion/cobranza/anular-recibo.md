# Anular un recibo

Anular un recibo lo pasa de **Pendiente** a **Cancelado**: el recibo no se cobrará.

## Pasos

1. Abre el recibo en estado **Pendiente**.
2. Pulsa el botón **Anular Recibo**.
3. Confirma la acción.

## Permisos requeridos

- Solo **Director General** o **Director Comercial** pueden anular recibos.

## Validaciones

- El recibo debe estar en **Pendiente**.

## Efectos

- El recibo queda en estado **Cancelado**.
- **No se cobra** ni se registra PCA.
- El recibo se conserva en el historial (no se borra).

## Diferencia con Cancelar pago

| Acción | Estado origen | Resultado |
|---|---|---|
| **Anular recibo** | Pendiente → Cancelado | No se cobrará nunca. |
| **Cancelar pago** | Pagado → Pendiente | Se revierte una cobranza hecha. |

## Notas

- Un recibo anulado permanece visible para auditoría.
- Al no cobrarse, no genera PCA ni avanza el Pagado Hasta.
