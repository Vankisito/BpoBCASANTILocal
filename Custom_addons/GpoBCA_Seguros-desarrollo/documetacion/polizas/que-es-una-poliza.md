# ¿Qué es una póliza?

Una **póliza** es el contrato entre un **contratante** y una **aseguradora** que se registra en el sistema para administrar su vigencia, su plan de pagos y la cobranza asociada. Es la unidad central de la operación de seguros: de ella dependen los recibos, la cobranza y el cálculo de la PCA.

## Para qué sirve

- Registrar el contrato vigente con todos sus datos (aseguradora, producto, ramo, agentes, montos y vigencia).
- Generar automáticamente el **plan de recibos** (pagos a lo largo de la vigencia).
- Servir de base para **conciliar la cobranza** recibida de las aseguradoras.
- Alimentar los **reportes de cartera y de PCA**.

## Qué contiene a alto nivel

| Dato | Descripción |
|---|---|
| **Número de póliza** | Identificador único por aseguradora. |
| **Aseguradora** | Compañía emisora (MetLife, Qualitas, etc.). |
| **Producto / Ramo** | Producto contratado y su familia (Vida, GMM, Autos, etc.). |
| **Contratante y asegurado** | Personas vinculadas al contrato. |
| **Agente / Promotoría** | Quién vende la póliza y a qué promotoría pertenece. |
| **Vigencia** | Fecha de inicio y fin de la cobertura. |
| **Periodicidad y primas** | Frecuencia de pago y montos correspondientes. |
| **Coberturas y beneficiarios** | Lo que ampara el contrato y a quién se paga. |

## Relación con otros elementos

```text
Aseguradora ── 1:N ── Póliza ── 1:N ── Recibo
                         │
                         ├── Agente (vendedor)
                         ├── Contratante / Asegurado
                         └── Producto / Ramo / Coberturas
```

> La póliza se registra en el menú **Pólizas** del área Gestión de Seguros. Antes de confirmarla permanece en estado **Borrador** y todavía no genera plan de pagos.
