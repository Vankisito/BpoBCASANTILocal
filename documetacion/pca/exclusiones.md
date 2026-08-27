# Exclusiones de PCA

Algunos recibos quedan **excluidos** del cálculo de PCA; en esos casos la PCA es 0 y se registra el motivo.

## Exclusiones por ramo

### Vida

| Exclusión | Motivo registrado |
|---|---|
| Producto **capitalizable / aportación adicional** | "Aportación adicional (producto capitalizable)" |
| **Temporalidad < 10 años** (si se capturó) | "Temporalidad < 10 años" |

> La temporalidad 0 o sin capturar se interpreta como permanente → no excluye.

### GMM

| Exclusión | Motivo |
|---|---|
| **Coaseguro ≤ 5%** | "Coaseguro ≤ 5%" |

## Otras causas de PCA en 0

Además de las exclusiones por producto, la PCA es 0 cuando:

- El ramo **no es soportado** por el calculador ("Ramo no soportado...").
- **No hay factor vigente** ("Sin factor PCA vigente").

## Qué muestra el recibo

Si la PCA es 0, el recibo guarda:

- `pca_aplicada = 0`.
- `factor_aplicado = 0`.
- `motivo_exclusion_pca` = el motivo que aplica.

## Notas

- Las exclusiones se evalúan **antes** de aplicar cualquier factor.
- Una exclusión no impide que el recibo se pague; solo anula su PCA.
