# Recibo pagado

Un recibo en estado **Pagado** tiene la cobranza registrada. Su PCA y su factor quedan **congelados**.

## Qué significa

- El pago fue registrado (manual o por archivo) con su **fecha de pago** y **conducto**.
- La **PCA** y el **factor aplicado** quedan congelados e inmutables.
- Queda registrado el **agente** y la **promotoría** que estaban al momento del pago (fotografía inmutable).

## Cómo se marca

El recibo se marca **Pagado** al:

- Registrarse un pago manual (`Registrar Pago`), o
- Procesarse un archivo de **cobranza** que lo incluya.

## Qué queda registrado

| Dato | Descripción |
|---|---|
| Fecha de pago | Cuándo se cobró. |
| Conducto | Vía de pago utilizada. |
| Prima neta / total | Importes del pago. |
| Agente / promotoría | Quién vendía al momento del pago (foto). |
| PCA aplicada | Valor de PCA congelado. |
| Factor aplicado | Factor de PCA usado. |
| Motivo exclusión | Si la PCA fue 0 (excluida), por qué. |
| Línea de bitácora | Origen si vino de un archivo. |

## Qué se actualiza en la póliza

- Se actualiza el **Pagado Hasta** de la póliza.
- Al pagar el último recibo pendiente de la anualidad, el sistema puede generar la **siguiente anualidad** (ver *siguiente-anualidad*).

## Reglas de protección

- **La PCA de un recibo pagado no se puede editar** (inmutable).
- Solo un rol autorizado puede **cancelar el pago** para revertir el recibo a pendiente (ver *cobranza/cancelar-pago*).
