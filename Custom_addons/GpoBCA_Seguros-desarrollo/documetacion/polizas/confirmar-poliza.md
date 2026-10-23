# Confirmar una póliza

Confirmar la póliza la pasa de **Borrador** a **Activa** y genera el **plan de pagos**. Es el paso que la deja operativa para la cobranza.

## Acción

- En el formulario de la póliza, en la barra superior, pulsa el botón **Confirmar**.
- Solo está disponible cuando la póliza está en estado **Borrador**.

## Validaciones previas

Antes de confirmar, el sistema valida:

- Que la póliza esté en **Borrador**.
- Que los **beneficiarios** de Vida sumen **100%** (si aplica).

## Qué cambia al confirmar

1. El estado pasa a **Activa**.
2. El sistema **genera el plan de pagos** del primer año:
   - según la **periodicidad**, crea los recibos correspondientes del año vigente;
   - cada recibo queda en estado **Pendiente**.
3. Los campos principales de la póliza quedan de **solo lectura** (aseguradora, producto, fechas, periodicidad, etc.).

## Notas

- El resto del término de la póliza se genera **año por año**: al pagar el último recibo pendiente (o con el botón manual) se genera la siguiente anualidad.
- No se generan cientos de recibos de golpe en pólizas largas; solo la anualidad vigente.
