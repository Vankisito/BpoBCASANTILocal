# Recibo pendiente

Un recibo en estado **Pendiente** está por cobrar dentro del plan de pagos de la póliza.

## Qué significa

- Es un recibo aún **sin pago** registrado.
- Es el candidato a cobrar en el siguiente paso de la cobranza.
- Conserva los importes del plan (prima neta, modal, total) y su ventana de cobertura.

## Qué acciones puede hacer el usuario

| Acción | Descripción |
|---|---|
| **Registrar pago** | Cobrar el recibo (manual o por archivo de cobranza). |
| **Anular recibo** | Cancelar el recibo (no se cobrará). |

> Solo se permite pagar el pendiente **más antiguo** según la regla FIFO (ver *regla-fifo*).

## Registro manual de un recibo pendiente

- Desde el formulario del recibo, el botón **Registrar Pago** cobra el recibo (ver *cobranza/registrar-pago-manual*).
- Es **obligatorio** indicar el **conducto** de pago en el flujo manual.

## Generación

- Los recibos pendientes nacen al **confirmar** la póliza.
- Puede haber varios pendientes simultáneos (p. ej. en periodicidad mensual), siempre que se paguen en orden.

## Notas

- Mientras un recibo esté pendiente no hay PCA asociada.
- No se permite crear un recibo nuevo a mano si la póliza ya tiene un pendiente: el sistema te redirige al pendiente existente.
