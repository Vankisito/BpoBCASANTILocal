# Primas e importes

La póliza captura los montos económicos del contrato y la moneda en que se expresa.

## Campos principales

| Campo | Descripción | Notas |
|---|---|---|
| **Prima anual** | Prima total anual del contrato. | Base del cálculo del plan de pagos. |
| **Prima fraccionada** | Prima por recibo. | Se calcula como prima anual / número de períodos. |
| **Recargo por fraccionamiento** | Recargo por pagar la prima en partes. | Informativo. |
| **Recargo fijo** | Recargo fijo de la póliza. | Informativo. |
| **Suma asegurada** | Monto asegurado. | Informativo. |
| **IVA** | Impuesto correspondiente. | Solo GMM; no entra en la PCA. |
| **Moneda** | MXN, USD, etc. | Define la moneda de los importes y del cálculo de PCA. |

## Cómo se capturan o calculan

- La **prima anual** y los recargos se capturan (o se llenan desde la carga de cartera).
- La **prima fraccionada** se usa en la generación del plan de recibos:
  - `prima por recibo = prima_anual / recibos_por_año`
- La **moneda** es relevante para el cálculo de PCA en pólizas extranjeras (ver sección PCA → multimoneda).

## Relación con el recibo

Cada **recibo** del plan de pagos contiene:

| Campo del recibo | Origen |
|---|---|
| Prima modal | Monto del período (equivale a la prima fraccionada). |
| Prima neta | Base para el cálculo de PCA. |
| Prima total | Lo que paga el cliente (neta + recargos + impuestos). |
| Recargo | Recargo del período. |
| Moneda | Moneda de la póliza. |

## Notas de negocio

- La **primera neta** de cada recibo es la **base de la PCA** (ver sección PCA).
- El IVA y el recargo **no** entran en el cálculo de la PCA.
