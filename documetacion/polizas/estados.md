# Estados de la póliza

Estos son los estados exactos de una póliza y las transiciones permitidas entre ellos.

## Estados

| Estado | Significado |
|---|---|
| **Borrador** | Recién creada / en captura. Editable, sin plan de pagos. |
| **Activa** | Confirmada, con plan de pagos generado. Operativa para cobranza. |
| **Vencida (Expirada)** | El plazo contractual llegó a su fecha de fin. |
| **Cancelada** | Cancelada; no se generan nuevas cobranzas (los pagos históricos se conservan). |

> Nota: la clave interna de "vencida" se mantiene por compatibilidad, pero su significado operativo es **Expirada** (fin del plazo), distinto del **estatus de pago** "Vencido".

## Transiciones permitidas

```text
Borrador ──Confirmar──> Activa
Activa   ──Fin de vigencia (tiempo)──> Vencida (Expirada)
Borrador/Activa/Vencida ──Cancelar──> Cancelada
```

## Estados relacionados (no confundir)

- **Estatus de pago** (`estatus_pago`): Al corriente / Vencido / Suspendido. Es un dato derivado de la salud de pago, no del plazo contractual.
- **Estado del recibo**: Pendiente / Pagado / Cancelado (ver sección Recibos).

## Reglas

- Solo las pólizas en **Borrador** se pueden confirmar.
- Desde **Borrador** se puede cancelar; los recibos pendientes se conservan para auditoría.
- Una póliza **cancelada** mantiene su historial de pagos (no se borra).
