# PCA por ramo

El cálculo de PCA varía según el **ramo** de la póliza (Vida, GMM, etc.).

## Ramos soportados por el calculador (MetLife)

| Ramo | Consideraciones |
|---|---|
| **Vida** | Factores por producto y moneda; exclusiones por aportación adicional y temporalidad. |
| **GMM** | Factores según coaseguro y deducible; exclusión por coaseguro bajo. |

## Vida

- El factor depende del **producto** y de la **moneda** de la póliza.
- Se excluyen del cálculo:
  - **Aportación adicional** (producto capitalizable).
  - **Temporalidad menor a 10 años** (si se capturó y es < 10).

## GMM

- El factor se elige según los umbrales de:
  - **coaseguro**;
  - **deducible**.
- Se excluye la póliza con **coaseguro ≤ 5%**.
- Se normaliza el coaseguro (fracción vs puntos porcentuales) antes de comparar con los factores.

## Implicación en reportes

- Los reportes de PCA incluyen la dimensión **ramo**.
- La PCA acumulada se puede consultar por ramo para analizar la composición de la producción.

## Notas

- Los ramos Autos/Daños pueden no tener calculador todavía (placeholder).
- La PCA se expresa siempre en MXN, aunque el ramo/produto esté en otra moneda.
