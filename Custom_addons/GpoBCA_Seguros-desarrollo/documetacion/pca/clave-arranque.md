# Clave de Arranque

La **Clave de Arranque** es la primera clave que la aseguradora asigna al agente al iniciar su carrera, **sin certificar**.

## Qué es

- Es el estado inicial del agente en una aseguradora (tras el puente agente–aseguradora).
- Queda registrado en el **puente** (`res.partner.agente.aseguradora.estado = 'clave_arranque'`).

## Su efecto sobre la PCA

> **La Clave de Arranque NO computa PCA.**

- Un agente recién habilitado en Clave de Arranque **no debe computar** producción.
- Sus recibos pagados pueden tener PCA calculada en el recibo, pero **no aparecen** en los reportes oficiales de PCA.
- El pase a definitiva es un proceso interno posterior que sí habilita el cómputo.

## Relación con reclutamiento

- La Clave de Arranque se asienta en el candidato (campo `bca_clave_arranque`) y se materializa en el puente al emitir la cédula.
- Es distinta de la clave definitiva (que computa).

## Resumen

| Estado | ¿Computa PCA? |
|---|---|
| Prospecto | No |
| Clave de Arranque | No |
| Clave Definitiva | Sí |

## Notas

- El estado es **por aseguradora**: un agente puede estar en Arranque en una aseguradora y en Definitiva en otra.
- Para que su PCA cuente en una aseguradora, debe estar en Definitiva en esa misma aseguradora.
