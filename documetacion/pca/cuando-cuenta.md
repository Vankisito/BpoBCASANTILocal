# Cuándo cuenta un pago para PCA

No todos los pagos aparecen en los reportes de PCA. Hay una **condición exacta** de elegibilidad.

## Condición para que un pago cuente en los reportes oficiales de PCA

Un recibo pagado cuenta para PCA cuando se cumplen **todas** las siguientes:

1. El recibo está en estado **Pagado**.
2. El agente tiene un registro en el **puente agente–aseguradora** (`res.partner.agente.aseguradora`).
3. La **aseguradora del puente coincide** con la aseguradora de la póliza.
4. El estado del puente en esa aseguradora es **`clave_definitiva`**.

```text
recibo pagado
  + puente agente-aseguradora
  + misma aseguradora
  + estado = clave_definitiva
      ==> cuenta para PCA
```

## Clave de Arranque NO cuenta

- Un agente en **Clave de Arranque** puede tener recibos pagados con PCA calculada, **pero no aparece** en los reportes oficiales de PCA.
- Solo la **Clave Definitiva** habilita el cómputo oficial (ver *clave-arranque* y *clave-definitiva*).

## Nota importante sobre el recibo en sí

- El **recibo** calcula y congela la PCA en cuanto se paga (independientemente del estado del agente).
- La exigencia de *clave_definitiva* se aplica en los **reportes** de PCA, no en el cálculo del recibo.

## Resumen

| Situación | ¿Cuenta en reportes PCA? |
|---|---|
| Recibo pendiente | No |
| Recibo pagado, agente en Clave de Arranque | No |
| Recibo pagado, agente en Clave Definitiva | Sí |
| Recibo pagado sin factor vigente (PCA 0) | No aporta monto |
