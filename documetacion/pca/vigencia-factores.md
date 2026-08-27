# Vigencia de los factores

El factor de PCA que se aplica depende de la **fecha de pago** del recibo.

## Cómo se determina el factor vigente

El calculador busca el factor que cumpla, a la fecha de pago:

- Pertenece a la **aseguradora** de la póliza.
- Corresponde al **ramo** de la póliza.
- Está **activo**.
- Su `vigencia_desde` es **<= fecha de pago**.
- Su `vigencia_hasta` es **no definida** o **>= fecha de pago**.

## En Vida además tiene que coincidir

- El **producto** de la póliza.
- La **moneda** de la póliza.

## En GMM

- Se filtran los candidatos por los umbrales de **coaseguro** y **deducible**, y se toma el más específico (mayor deducible, luego mayor coaseguro).

## Ejemplo

```text
Fecha de pago: 2026-03-01
Factor con vigencia 2026-01-01 → 2026-12-31 ?  Sí → aplica
Factor inactivo o sin vigencia que cubra esa fecha ?  No
```

## Consecuencia

- Un cambio de tabla de factores no afecta pagos anteriores: cada pago usa el factor **vigente a su fecha**.
- Si a la fecha de pago no hay factor vigente, la PCA es 0 con motivo "Sin factor PCA vigente".
