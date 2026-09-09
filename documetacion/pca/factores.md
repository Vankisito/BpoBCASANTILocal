# Factores de PCA

Los **factores** de PCA son las tasas de la aseguradora que se aplican a la prima neta para obtener la PCA.

## Qué son

```text
PCA = Prima Neta × Factor
```

- Cada factor pertenece a una **aseguradora** y a un **ramo**.
- Tiene una **vigencia** (desde/hasta) y un estado activo/inactivo.
- En **Vida**, el factor se asocia a un **producto** y a una **moneda**.

## De dónde se obtienen

- Son datos de **catálogo** del sistema (`bca.factor.pca`), configurados / sembrados por aseguradora.
- Por ejemplo, los factores de MetLife se cargan como datos del módulo (tabla 2026) y son **actualizables** por la aseguradora.
- Para productos sin factor asignado, la PCA queda en 0 (ver *pca-en-cero*).

## Campos del factor

| Campo | Descripción |
|---|---|
| Aseguradora | A quién pertenece. |
| Ramo | Vida o GMM. |
| Factor | Valor multiplicador. |
| Productos | Productos asociados (Vida). |
| Moneda | Moneda a la que aplica (Vida). |
| Vigencia desde / hasta | Período de validez. |
| Activo | Si está en uso. |
| Coaseguro / Deducible mín/máx | Umbrales (GMM). |

## Notas

- Si falta el factor para el producto/moneda/fecha del recibo, la PCA es 0 con el motivo "Sin factor PCA vigente".
- Los factores de GMM no discriminan por moneda.
