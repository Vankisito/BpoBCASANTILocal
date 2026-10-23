# PCA en moneda extranjera (multimoneda)

Cuando la póliza está en una **moneda distinta de MXN**, la PCA se ajusta y se convierte a **MXN**.

## Regla (D-08)

> La PCA se expresa **SIEMPRE en MXN**.

## Cómo se maneja

1. Se calcula `PCA = prima_neta × factor` en la **moneda de la póliza**.
2. Se convierte el resultado a **MXN** usando `res.currency` a la **fecha de pago**.

## Selección del factor según moneda (Vida)

- En **Vida**, la tabla de factores distingue por **moneda**:
  - p. ej. TempoLife: 100% en MXN / 80% en USD.
- Se selecciona la fila cuyo `currency_id` coincide con la **moneda de la póliza**.
- Así, una póliza USD recibe su factor USD (conserva el ajuste del 80%).

## GMM

- Los factores GMM son MXN y no discriminan por moneda.

## El recibo

- El recibo guarda `pca_currency_id = MXN` (moneda de la PCA), distinta de la moneda de la póliza.
- El campo `pca_currency_id` es el que usan los reportes, para que toda la PCA esté en MXN.

## Notas

- La conversión depende de la **fecha de pago** (tasa vigente a ese día).
- Si la póliza ya está en MXN, no hay conversión.
