# Beneficiarios

Los **beneficiarios** son las personas que recibirán el pago/amparo de la póliza. Se registran por póliza, principalmente en el ramo **Vida**.

## Datos requeridos por beneficiario

| Dato | Descripción |
|---|---|
| **Nombre del beneficiario** | Identificación de la persona. |
| **Parentesco** | Relación con el asegurado/contratante (cónyuge, hijo, etc.). |
| **Porcentaje** | Porcentaje del derecho al que tiene el beneficiario. |
| **Fecha de nacimiento** | Necesaria para dependientes GMM. |

## Cómo se agregan

1. En el formulario de la póliza, en **Beneficiarios**, agrega un registro.
2. Completa nombre, parentesco y porcentaje.
3. Repite por cada beneficiario (hasta el máximo permitido, p. ej. 10 en Vida).

## Regla de porcentajes

- En **Vida**, la suma de los porcentajes de los beneficiarios debe ser **exactamente 100%**.
- Si no suma 100%, la póliza no se puede confirmar hasta corregirlo.

## Carga masiva

- También se pueden importar beneficiarios desde el archivo de cartera, en la hoja **BENEFICIARIOS** (formato largo).
- Al procesar, la carga **reemplaza** los beneficiarios existentes de la póliza (semántica de reemplazo) y valida que los porcentajes sumen 100% en Vida.

## Notas

- Un contacto puede ser beneficiario en una póliza y tener su propio rol en otra.
- Los porcentajes se validan al confirmar la póliza.
