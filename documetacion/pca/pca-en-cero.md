# ¿Por qué la PCA aparece en cero?

Cuando un recibo pagado tiene PCA en 0, generalmente se debe a una de las siguientes causas.

## Causas más comunes

| Causa | Motivo registrado | Cómo revisarlo |
|---|---|---|
| **Exclusión por producto** | "Aportación adicional…" | Póliza Vida capitalizable / aportación adicional. |
| **Temporalidad corta** | "Temporalidad < 10 años" | Póliza Vida con temporalidad < 10 años. |
| **Coaseguro bajo** | "Coaseguro ≤ 5%" | Póliza GMM con coaseguro bajo. |
| **Sin factor vigente** | "Sin factor PCA vigente" | Producto/moneda sin factor configurado o factor fuera de vigencia. |
| **Ramo no soportado** | "Ramo no soportado por calculador…" | Podría ser un ramo sin calculador (p. ej. Autos). |

## Además: elegibilidad del agente

- Aunque el recibo tenga PCA calculada, si el agente **no está en Clave Definitiva** en esa aseguradora, **no aparece** en los reportes de PCA (ver *cuando-cuenta*).

## Cómo revisarlo

1. Abre el **recibo pagado** y consulta el campo **Motivo Exclusión PCA**.
2. Según el motivo:
   - productos capitalizables / temporalidad / coaseguro: son reglas de negocio; la PCA correctamente es 0.
   - sin factor: verifica en el catálogo de **factores** si el producto/moneda tiene factor activo y vigente.
3. Confirma que el agente esté en **Clave Definitiva** en la aseguradora de la póliza.

## Notas

- Una PCA en 0 por exclusión o falta de factor es comportamiento esperado y documentado.
- Si el motivo no aclara la causa, contacta a soporte con el recibo.
