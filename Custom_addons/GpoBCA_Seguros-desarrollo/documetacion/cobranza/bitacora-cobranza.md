# Bitácora de cobranza

La **bitácora** es el registro auditable e inmutable de cada corrida de importación de cobranza.

## Dónde se consulta

- Menú **Bitácoras de Importación** del área Gestión de Seguros.
- La bitácora se abre automáticamente al procesar una corrida.

## Qué muestra la cabecera

| Dato | Descripción |
|---|---|
| Folio | Identificador de la corrida. |
| Ejecutado por | Usuario que la procesó. |
| Fecha de ejecución | Cuándo corrió. |
| Aseguradora | Aseguradora de la corrida. |
| Ramo | Vida o GMM. |
| Nombre del archivo | Archivo subido. |
| Total de filas | Filas procesadas. |
| Recibos aplicados | Pagos aplicados. |
| Pólizas no encontradas | Referencias sin póliza. |
| Errores de procesamiento | Filas con error. |
| PCA total sesión | Suma de PCA de la corrida. |

## Detalle por línea

- Cada línea registra el número de fila, la **marca** (aplicado, advertencia, no encontrada, sin recibo, error, info) y el mensaje.
- Guarda el `numero_poliza_raw` para localizar referencias.

## Inmutabilidad

- La bitácora es **inmutable**: no se puede editar ni borrar (salvo administración/superusuario).
- Garantiza la auditoría de toda la cobranza.

## Notas

- La bitácora es el único reporte auditable de las cargas de cobranza.
- Se usa para auditar pagos aplicados y resolver no encontradas o errores.
