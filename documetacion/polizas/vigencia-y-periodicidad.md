# Vigencia y periodicidad

La **vigencia** define cuánto dura la cobertura de la póliza y la **periodicidad** define con qué frecuencia se paga.

## Campos

| Campo | Descripción | Notas |
|---|---|---|
| **Fecha de inicio** | Inicio de la vigencia | Obligatorio. Es anterior a la fecha de fin. |
| **Fecha de fin** | Fin de la vigencia | Obligatorio. Se sugiere automáticamente. |
| **Periodicidad** | Frecuencia de pago | Mensual, trimestral, semestral o anual. |

## Fecha de fin sugerida

El sistema puede **sugerir** la fecha de fin automáticamente (la deja editable):

- **Vida**: fecha de inicio + **temporalidad** (años).
- **Otros ramos**: fecha de inicio + **1 año**.

Si no hay temporalidad capturada, se usa la regla de 1 año.

## Periodicidad y plan de pagos

La periodicidad determina cuántos recibos se generan por año:

| Periodicidad | Recibos por año |
|---|---|
| Mensual | 12 |
| Trimestral | 4 |
| Semestral | 2 |
| Anual | 1 |

> El plan de pagos se genera al **confirmar** la póliza. La periodicidad define el número y monto de cada recibo.

## Notas

- La fecha de inicio debe ser siempre **anterior** a la fecha de fin; el sistema lo valida.
- Con el tiempo y la cobranza, el campo **Pagado Hasta** refleja hasta qué fecha está cubierta la póliza (ver sección Recibos).
