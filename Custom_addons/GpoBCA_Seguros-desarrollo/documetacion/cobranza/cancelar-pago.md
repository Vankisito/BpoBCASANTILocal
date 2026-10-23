# Cancelar un pago

Cancelar un pago **revierte** un recibo pagado a **Pendiente**, deshaciendo la cobranza.

> No confundir con **anular recibo** (ver *anular-recibo*).

## Pasos

1. Abre el recibo en estado **Pagado**.
2. Pulsa el botón **Cancelar Pago**.
3. Confirma la acción.

## Permisos requeridos

- Solo **Director General** o **Director Comercial** pueden cancelar pagos.
- El sistema valida el rol además de las ACL.

## Validaciones

- El recibo debe estar en **Pagado**.
- Solo se puede cancelar el **último** recibo pagado de la póliza (regla FIFO inversa):
  - no se permite cancelar un pago si hay otro recibo pagado con mayor número de recibo.

## Efectos

- El recibo vuelve a **Pendiente**.
- Se **limpia** la PCA, factor y datos del pago.
- El **Pagado Hasta** de la póliza puede retroceder al recibo anterior pagado.

## Notas

- La cancelación de un pago es una operación sensible, restringida a roles de dirección.
- El recibo no se elimina: sólo se revierte su estado.
