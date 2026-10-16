# ¿Qué es un recibo?

Un **recibo** es la **fracción de la prima** de una póliza que corresponde a un periodo de cobertura. Es la unidad de cobranza.

## Relación con la póliza

```text
Póliza ── 1:N ── Recibo
```

- Cada póliza tiene uno o más recibos según su **periodicidad** (mensual, trimestral, semestral, anual).
- Cada recibo tiene un **número** secuencial dentro de su póliza.
- El recibo define una ventana de cobertura (**Desde** / **Hasta**).

## Datos del recibo

| Dato | Descripción |
|---|---|
| **Folio** | Identificador único del recibo (se genera solo). |
| **Póliza** | Póliza a la que pertenece. |
| **Número de recibo** | Secuencia dentro de la póliza (1, 2, 3…). |
| **Cobertura Desde / Hasta** | Periodo al que corresponde. |
| **Prima modal / neta / total** | Importes del periodo (ver sección primas). |
| **Estado** | Pendiente, Pagado o Cancelado. |
| **Conducto** | Vía de pago (para cobranza). |

## Relación con cobranza y PCA

- Cuando un recibo se **paga**, se registra la cobranza.
- Al pagarse se **congela** la **PCA** del recibo (ver sección PCA).
- El recibo conserva una **fotografía inmutable** del agente y la promotoría que estaban al momento del pago.

> Los recibos se generan de forma automática al **confirmar** la póliza (primer año) y, posteriormente, al avanzar cada anualidad.
