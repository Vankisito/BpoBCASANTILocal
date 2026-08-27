# Errores de procesamiento

Durante una corrida de cobranza pueden presentarse distintos tipos de resultado. Este documento explica los errores comunes y cómo interpretarlos.

## Tipos de resultado por fila

| Marca | Significado |
|---|---|
| **Aplicado** | Pago registrado correctamente. |
| **Advertencia** | Pago aplicado, pero con aviso (p. ej. conducto sin coincidencia). |
| **No encontrada** | Póliza inexistente o de otra aseguradora. |
| **Sin recibo** | La póliza no tiene recibo pendiente. |
| **Error** | Fallo al procesar la fila (error inesperado o de validación). |

## Errores comunes

| Problema | Causa probable | Cómo revisarlo |
|---|---|---|
| Estructura inválida al iniciar | Faltan columnas requeridas | Compara con la plantilla del ramo. |
| Póliza no encontrada | Número distinto o aseguradora equivocada | Revisa `numero_poliza_raw` en la bitácora. |
| Sin recibo pendiente | Póliza ya pagada o sin recibos por cobrar | Consulta los recibos de la póliza. |
| Monto inválido | Formato de número incorrecto | Revisa el valor de la columna. |
| Fecha inválida | Formato de fecha distinto | Usa el formato esperado. |
| Error inesperado | Registro inconsistente o regla no aplicable | Contacta a soporte con la línea. |

## Interpretación en la bitácora

- La bitácora resume:
  - Total de filas.
  - Recibos aplicados.
  - Pólizas no encontradas.
  - Errores de procesamiento.
  - PCA total de la sesión.
- Cada línea de error mantiene el número de póliza original y el mensaje.

## Aislamiento por fila

- Cada fila se procesa en su propio **savepoint** (rollback aislado).
- El error de una fila **no detiene** las demás.
- Un `NotImplementedError` (parser placeholder) sí aborta todo el flujo.

## Notas

- Antes de reimportar, corrige las filas con error o resuelve la causa (alta de póliza, conducto, formato).
