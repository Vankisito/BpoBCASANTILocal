# Clave Definitiva

La **Clave Definitiva** es la clave firme del agente, ya **certificado** por la aseguradora.

## Qué es

- Es el nivel de carrera del agente en una aseguradora en el que ya está certificado.
- Solo este estado **computa PCA** de forma oficial.

## Su efecto sobre la PCA

> **La Clave Definitiva es la única que computa PCA.**

- El puente (`res.partner.agente.aseguradora.estado`) debe estar en `clave_definitiva` para que los recibos pagados del agente aparezcan en los reportes de PCA.
- La condición se evalúa contra la **aseguradora de la póliza** (no contra el estado global del contacto).

## Cómo se determina

- La fuente de verdad es el **puente agente–aseguradora** por aseguradora.
- El campo `bca_estado_agente` del contacto es solo un **resumen** (rollup) del mejor estado; los reportes de PCA **no** usan ese resumen.

## Ejemplo por aseguradora

| Aseguradora | Estado del puente | ¿Computa PCA en esa aseguradora? |
|---|---|---|
| MetLife | Clave Definitiva | Sí |
| Qualitas | Clave de Arranque | No |

## Resumen

| Estado | ¿Computa PCA? |
|---|---|
| Prospecto | No |
| Clave de Arranque | No |
| Clave Definitiva | Sí |

## Notas

- Un agente puede tener Clave Definitiva en una aseguradora y Arranque en otra.
- Si un recibo pagado pertenece a una aseguradora donde el agente está en Arranque, su PCA no aparecerá aunque el agente tenga definitiva en otra parte.
