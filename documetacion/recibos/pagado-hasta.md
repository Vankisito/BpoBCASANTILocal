# Pagado Hasta

**Pagado Hasta** es la fecha hasta la cual la póliza está cubierta por pagos efectivos.

## Qué es

- Es un campo **calculado** de la póliza.
- Indica hasta qué fecha hay cobertura respaldada por recibos **pagados**.
- Es la base para determinar el **estatus de pago** (Al corriente / Vencido).

## Cómo se actualiza

- Se recalcula automáticamente cuando cambia el estado o la fecha de un recibo.
- Al registrar el **pago de un recibo**, Pagado Hasta avanza hasta el `fecha_hasta` de ese recibo.
- Al **cancelar un pago**, Pagado Hasta puede retroceder al recibo anterior pagado.

## Reglas importantes

- **No se edita a mano**: es un campo computado gestionado por el sistema.
- En pólizas sin pagos registrados, puede apoyarse en el `pagado_hasta_inicial` declarado en la **carga de cartera** como punto de arranque.

## Relación con el estatus de pago

- **Al corriente**: la fecha efectiva (Pagado Hasta o Pagado Hasta inicial) más el **periodo de gracia** es >= hoy.
- **Vencido**: la fecha efectiva más el periodo de gracia ya pasó.
- **Suspendido**: override manual por suspensión administrativa.

## Notas

- Un cron diario recalcula el estatus de las pólizas activas para que envejezca con el tiempo.
- No confundir con la **fecha de fin** de la póliza (que es el término contractual).
