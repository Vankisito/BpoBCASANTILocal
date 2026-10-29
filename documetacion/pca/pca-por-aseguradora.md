# PCA por aseguradora

El cálculo y el reporte de PCA dependen de la **aseguradora** de la póliza.

## Cómo varía

- El **calculador** de PCA es específico por aseguradora (p. ej. `CalculadorPCAMetLife`).
- Cada aseguradora define sus **factores**, ramos y reglas.
- La PCA se expresa siempre en **MXN**.

## Elegibilidad por aseguradora

- El estado del agente se evalúa **por aseguradora**:
  - El puente agente–aseguradora debe estar en `clave_definitiva` en la **misma aseguradora** de la póliza.
- Un agente en Definitiva en MetLife pero en Arranque en Qualitas solo computa la PCA de las pólizas de MetLife.

## Factores

- Los **factores** de PCA se configuran por aseguradora, ramo y producto (ver *factores*).
- Un agente con pólizas en dos aseguradoras puede tener factores distintos.

## Reporte

- Los reportes de PCA (por agente/promotoría/consolidado) incluyen la dimensión **aseguradora** y solo muestran pagos con el agente en `clave_definitiva` en esa aseguradora.

## Resumen

```text
Póliza de MetLife ──> calculador MetLife ──> factor MetLife
   └─> agente en Definitiva en MetLife? ──> Sí: cuenta; No: no cuenta
```

## Notas

- Si la aseguradora no tiene parser/calculador implementado (placeholder), la cobranza/PCA no está disponible para ella.
