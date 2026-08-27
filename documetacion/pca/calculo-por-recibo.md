# Cálculo de PCA por recibo

Este es el cálculo exacto de la PCA por cada recibo pagado.

## Fórmula

```text
PCA (moneda de la póliza) = Prima Neta × Factor
PCA (en MXN) = conversión a MXN si la póliza es en otra moneda
```

## Pasos

1. Verificar que el **ramo** sea soportado por el calculador (Vida/GMM). Si no → PCA 0 (ramo no soportado).
2. Evaluar **exclusiones** (ver *exclusiones*). Si hay exclusión → PCA 0 con el motivo.
3. Buscar el **factor vigente** a la fecha de pago (ver *vigencia-factores*). Si no hay → PCA 0 (sin factor).
4. Calcular `PCA = prima_neta × factor` (en la moneda de la póliza).
5. Convertir a **MXN** si corresponde (ver *multimoneda*).

## Cuándo se calcula

- Al **registrar el pago** de un recibo (manual o por archivo).
- Se usa la **prima neta** del recibo.
- El calculador necesita la **fecha de pago** para elegir el factor y la tasa de conversión.

## Resultado

- La PCA y el **factor aplicado** se guardan en el recibo.
- Si la PCA es 0, se guarda el **motivo de exclusión**.

## Notas importantes

- La PCA se calcula **antes** de marcar el recibo como pagado (usando la prima del plan).
- Se expresa SIEMPRE en **MXN** (decisión D-08).
