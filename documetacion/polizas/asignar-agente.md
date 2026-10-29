# Asignar agente y promotoría

El **agente** es el vendedor responsable de la póliza y debe pertenecer a la red comercial (tipo *Agente*).

## Cómo se busca y asigna el agente

1. En el formulario de la póliza, dentro de **Asignación organizacional**, elige el campo **Agente**.
2. Busca el contacto del agente. El selector solo muestra contactos de tipo **Agente**.

> El campo solo permite elegir contactos marcados como *Agente* en la clasificación BCA. No se pueden seleccionar contratantes, promotorías ni personas sin tipo.

## Promotoría

- La **Promotoría** se completa **automáticamente** con la promotoría actual del agente (el `parent_id` del agente).
- Es un campo de **solo lectura**: no se edita a mano.
- Si el agente cambia de promotoría, las pólizas nuevas toman la nueva promotoría.

## Cambio posterior de agente

Si después de crear la póliza se necesita reasignar el agente, se usa la acción **Cambiar agente**:

- Registra un historial **inmutable** del cambio (agente anterior, nuevo, promotoría anterior/nueva y motivo).
- Solo se puede asignar un contacto de tipo **Agente**.
- La PCA de pagos ya registrados se mantiene bajo el agente que estaba al momento del pago (fotografía del recibo), no se mueve con el cambio.

## Notas

- La póliza exige agente obligatorio: no se puede guardar sin un agente válido.
- La asignación del agente define la cartera atribuible a ese agente y a su promotoría.
