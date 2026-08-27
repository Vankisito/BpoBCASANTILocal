# Seleccionar aseguradora, ramo y producto

La selección del producto sigue una **cascada** que reduce las opciones disponibles según la aseguradora y el ramo elegidos.

## Orden de selección

1. **Aseguradora**: se elige primero.
2. **Ramo**: se autocompleta desde el producto, pero sirve de filtro intermedio.
3. **Producto**: se elige de entre los productos de esa aseguradora y ese ramo.
4. **Coberturas**: se eligen de entre las que ofrece el producto seleccionado.

## Dependencias entre campos

- El campo **Producto** solo permite seleccionar productos de:
  - la aseguradora elegida (`bca_aseguradora_id`);
  - el ramo elegido (`bca_ramo`);
  - marcados como producto de seguro.
- Si se cambia la **aseguradora** o el **ramo**, el producto seleccionado se limpia si ya no cumple los nuevos filtros.
- Si se cambia el **producto**, las **coberturas** elegidas se limpian (dejan de pertenecer al producto contratado).

## Ejemplo

```text
Aseguradora: MetLife
   └─ Ramo: Vida
        └─ Producto: TempoLife
             └─ Coberturas: Cobertura Básica (Vida)
```

> La regla asegura que nunca pueda asociarse un producto de otra aseguradora o ramo, ni coberturas que ese producto no ofrece.
