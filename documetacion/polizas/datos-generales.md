# Datos generales de la póliza

Los campos generales del registro de póliza se encuentran en el formulario. A continuación se listan los principales y cuáles son obligatorios.

## Campos obligatorios

| Campo | Descripción |
|---|---|
| **Número de póliza** | Identificador único del contrato. Debe ser único por aseguradora. |
| **Aseguradora** | Compañía emisora. Debe ser un contacto de tipo *Aseguradora*. |
| **Producto** | Producto contratado. Debe pertenecer a la aseguradora y ramo elegidos. |
| **Agente** | Agente responsable de la venta. Debe ser un contacto de tipo *Agente*. |
| **Contratante** | Persona que firma el contrato. |
| **Fecha de inicio** | Inicio de la vigencia. |
| **Fecha de fin** | Fin de la vigencia. Debe ser posterior al inicio. |
| **Periodicidad** | Frecuencia de pago (mensual, trimestral, semestral, anual). |

## Campos informativos / opcionales

| Campo | Descripción |
|---|---|
| **Ramo** | Se autocompleta desde el producto, aunque es editable como filtro. |
| **Asegurado** | Persona cuya vida/bienes se aseguran. Puede ser distinta del contratante. |
| **Promotoría** | Se completa sola desde el agente; de solo lectura. |
| **Prima anual** | Prima total anual del contrato. |
| **Prima fraccionada** | Prima por recibo (prima anual / número de períodos). |
| **Recargos** | Recargo por fraccionamiento y recargo fijo. |
| **Suma asegurada** | Monto asegurado. |
| **IVA** | Impuesto correspondiente. |

## Estados internos

- **Borrador**: recién creada, editable, sin plan de pagos.
- **Activa**: confirmada, con plan de pagos generado.
- **Vencida (Expirada)**: el plazo contractual llegó a su fecha de fin.
- **Cancelada**: cancelada; no se generan nuevas cobranzas.

## Notas

- **Estatus de pago** (Al corriente / Vencido / Suspendido) es un dato derivado de la salud de pago, distinto del estado de la póliza.
