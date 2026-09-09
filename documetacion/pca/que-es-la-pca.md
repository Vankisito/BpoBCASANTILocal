# ¿Qué es la PCA?

La **PCA** (Prima Computable) es la cantidad que se le acredita al agente cuando se paga un recibo de una póliza. Es la base para medir la producción y liquidar comisiones.

## Qué mide

- Es la **prima neta** del recibo ajustada por un **factor** de la aseguradora:

```text
PCA = Prima Neta × Factor
```

- Se calcula por cada **recibo pagado**.
- Se expresa siempre en **MXN** (aunque la póliza sea en otra moneda).

## Para quién es relevante

| Audiencia | Relevancia |
|---|---|
| **Agente** | Es su producción acreditada (su "PCA"). |
| **Promotoría** | Acumula la PCA de sus agentes. |
| **Dirección / Directores** | Miden producción consolidada y por red. |

## Relación con el cobro

- **No cualquier pago cuenta para PCA.** La PCA solo es oficial en los reportes cuando el agente cumple la condición de elegibilidad (ver *cuando-cuenta*).
- El recibo, al pagarse, **congela** la PCA calculada (ver *congelamiento*).

## Concepto

```text
Recibo Pagado
   └─> Prima Neta
        └─> × Factor (según aseguradora, ramo, producto y fecha)
             └─> PCA (en MXN)
```

## Notas

- La PCA se consulta en los **reportes** por agente, promotoría y consolidado (ver sección Reportes).
- Está atada a la **fotografía del agente** al momento del pago, no al agente actual de la póliza.
