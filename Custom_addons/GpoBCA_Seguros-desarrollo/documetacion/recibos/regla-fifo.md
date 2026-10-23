# Regla FIFO de cobranza

La regla **FIFO** (First In, First Out) define el orden en que se aplican los pagos a los recibos de una póliza.

## Regla exacta

> **Siempre se paga primero el recibo pendiente más antiguo** (el de menor `numero_recibo`).

- Si intentas pagar un recibo que **no** es el pendiente más antiguo, el sistema lo **bloquea** con un error:
  - *"Debe pagarse el recibo X antes que el Y (FIFO)."*

## Ejemplo

En una póliza mensual con recibos 1, 2 y 3 pendientes:

```text
Recibo 1 ──se paga primero──> Pagado
Recibo 2 ──se paga después──> Pagado
Recibo 3 ──se paga al final──> Pagado
```

No se puede pagar el recibo 3 sin antes pagar el 1 y el 2.

## Aplica en ambos flujos

- **Pago manual** (Registrar Pago): valida por FIFO.
- **Cobranza por archivo**: el parser respeta la misma regla al aplicar cada línea.

## Reversa (cancelar pago)

- Al **cancelar un pago**, solo se permite revertir el **último** recibo pagado (el de mayor `numero_recibo` entre los pagados), para no dejar un pendiente antes de un pagado.

## Notas

- El orden FIFO garantiza coherencia en el **Pagado Hasta** y en la atribución de la cobranza.
