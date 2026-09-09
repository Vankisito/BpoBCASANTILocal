# Contratante y asegurado

En una póliza intervienen dos roles de persona que pueden o no ser la misma.

## Contratante

- Es la persona que **firma el contrato** y que **paga** la prima.
- Es un contacto (`res.partner`) asociado a la póliza mediante el campo **Contratante**.
- Puede ser un individuo (persona física) o una entidad.

## Asegurado

- Es la persona cuya **vida o bienes** están amparados por la póliza.
- También es un contacto, asociado mediante el campo **Asegurado**.
- **Puede ser distinto del contratante**: por ejemplo, un familiar puede ser el asegurado mientras el contratante paga.

## Diferencias

| Aspecto | Contratante | Asegurado |
|---|---|---|
| Rol | Firma y paga | Es la persona/bien asegurado |
| Campo en póliza | Contratante | Asegurado |
| ¿Puede ser el mismo? | Sí, puede coincidir con el asegurado | Sí |
| ¿Obligatorio? | Sí | Depende del ramo (visible en Vida/GMM) |

## Cómo se asignan

1. En el formulario de la póliza, en el grupo de **Asignación organizacional**.
2. Busca el contacto en el campo **Contratante** o **Asegurado** (opción de buscar o crear sin abrir el detalle).
3. Si el asegurado es el mismo que el contratante, se puede apuntar el campo Asegurado al mismo contacto.

## Notas

- Un mismo contacto puede ser contratante de una póliza y asegurado de otra.
- El sistema calcula automáticamente los indicadores *Es contratante* / *Es asegurado* a partir de las pólizas, para mostrarlos en el contacto.
