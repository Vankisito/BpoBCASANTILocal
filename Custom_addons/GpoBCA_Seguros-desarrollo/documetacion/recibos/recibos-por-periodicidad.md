# Recibos según periodicidad

La **periodicidad** elegida en la póliza determina el **número** y el **monto** de los recibos de cada año.

## Número de recibos por periodicidad

| Periodicidad | Recibos por año | Prima por recibo |
|---|---|---|
| Mensual | 12 | Prima anual / 12 |
| Trimestral | 4 | Prima anual / 4 |
| Semestral | 2 | Prima anual / 2 |
| Anual | 1 | Prima anual |

## Ejemplo con prima anual de 12,000

| Periodicidad | Nº recibos/año | Prima por recibo |
|---|---|---|
| Mensual | 12 | 1,000 |
| Trimestral | 4 | 3,000 |
| Semestral | 2 | 6,000 |
| Anual | 1 | 12,000 |

## Cómo se materializa

- Al **confirmar** la póliza se crea solo la **anualidad vigente** (los recibos del año en curso), no todo el término.
- Al terminar cada anualidad (pagando el último recibo pendiente) se genera la siguiente, continuando la numeración.
- El último recibo de la póliza se **recorta** a la fecha de fin de vigencia.

## Notas

- Este comportamiento evita generar cientos de recibo de golpe en pólizas largas.
- La periodicidad es un dato obligatorio de la póliza (default: anual).
