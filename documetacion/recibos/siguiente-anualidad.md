# Siguiente anualidad

La póliza avanza de anualidad **año por año**: al terminar la anualidad vigente se genera la siguiente, hasta cubrir todo el término.

## Cuándo ocurre

La siguiente anualidad se genera:

1. **Automáticamente** al pagar el **último recibo pendiente** de la anualidad vigente, o
2. **Manualmente** con el botón **Generar siguiente anualidad** (solo en pólizas **Activas**).

## Qué se genera

- Se crean los recibos del **año siguiente** con su periodicidad correspondiente.
- Se continúa la **numeración** a partir del último recibo existente.
- Los recibos quedan en estado **Pendiente**.

## Validaciones

- La generación automática ocurre al pagar el último pendiente, **si aún queda término** por cubrir.
- La generación manual solo aplica a pólizas **activas** **sin** recibos pendientes en la anualidad actual.
- No se genera nada si ya se llegó a la **fecha de fin** de la póliza.

## Ejemplo

Póliza anual de 10 años (2026–2036):

```text
Confirmar (2026)  ──> Recibos año 1
Pagar último      ──> Genera año 2
Pagar último      ──> Genera año 3
... 
(fin en 2036, no se genera más)
```

## Notas

- Este diseño evita crear cientos de recibos de golpe: solo existe la anualidad vigente y la siguiente se va generando.
- La numeración y ventanas de cobertura se mantienen coherentes con el plan.
