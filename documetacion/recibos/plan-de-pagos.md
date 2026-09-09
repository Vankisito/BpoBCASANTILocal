# Plan de pagos

El **plan de pagos** es el conjunto de recibos de una póliza distribuidos a lo largo de su vigencia.

## Cuándo se genera

- Se genera **automáticamente al confirmar** la póliza (ver *confirmar-poliza*), creando los recibos del **primer año** vigente.
- El resto del término se genera **año por año** (ver *siguiente-anualidad*), para no crear cientos de recibos de golpe.

## Cómo se calcula

El número de recibos por año depende de la **periodicidad**:

| Periodicidad | Recibos por año |
|---|---|
| Mensual | 12 |
| Trimestral | 4 |
| Semestral | 2 |
| Anual | 1 |

La **prima por recibo** = `prima_anual / recibos_por_año`.

## Cobertura de cada recibo

- Cada recibo recibe una ventana **Desde** / **Hasta** dentro del año.
- El último recibo de la póliza se recorta a la **fecha de fin** de la vigencia.

## Reglas de protección

- El plan **no se regenera** si ya hay recibos pagados (evita perder el historial).
- Si solo hay recibos **pendientes** de un intento previo, se descartan y se recrean al regenerar.

## Carga de cartera

- En la **carga de cartera**, el plan se ancla al `pagado_hasta_inicial` declarado: solo se generan recibos **posteriores** a esa fecha, sin crear recibos históricos pagados.

## Notas

- Los recibos del primer año nacen en estado **Pendiente**.
- El avance a la siguiente anualidad se dispara al pagar el último recibo pendiente o con el botón manual (ver *siguiente-anualidad*).
