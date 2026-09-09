# Agente, cobranza y PCA

La relación entre **agente**, **cobranza** y **PCA** es el núcleo del flujo de producción.

## Flujo conceptual

```text
Agente (bca_tipo='agente')
   │   pertenece a una Promotoría
   │   tiene puente con una Aseguradora (clave/estado)
   ▼
Póliza asignada al Agente
   │
   ▼
Recibos (plan de pagos)
   │
   ▼
Cobranza (el recibo se paga)
   │
   ▼
PCA (se acredita al agente que estaba al pagar)
```

## Puntos clave

- La **póliza** se asigna a un agente. La **promotoría** se deriva del agente.
- Al **pagar** un recibo, se toma una **fotografía inmutable** del agente y promotoría.
- La **PCA se atribuye** al agente de esa fotografía (no al agente actual de la póliza si cambió después).
- Para que la PCA sea **oficial** en reportes, el agente debe estar en **Clave Definitiva** para esa aseguradora.

## Atribución correcta

```text
Pago de la póliza
   └─> recibo.agente_id (quién vendía al pagar)  → PCA de ese agente
   └─> recibo.promotoria_id (su promotoría)      → PCA de esa promotoría
```

## Notas

- Si el agente cambia después del pago, la PCA **no se mueve**: sigue al agente original del pago.
- El estado del agente (Arranque/Definitiva) determina si su PCA aparece en los reportes.
