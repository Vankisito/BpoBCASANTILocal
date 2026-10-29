# Pólizas no encontradas

Cuando el archivo de cobranza referencia una póliza que no existe en el sistema, se registra como **póliza no encontrada**.

## Qué pasa

- La fila se marca con resultado **no encontrada**.
- El pago **no se aplica**.
- La línea de la bitácora se registra con el número de póliza tal como vino en el archivo (`numero_poliza_raw`).
- Al final, la bitácora reporta el contador **Pólizas No Encontradas**.

## Cómo se resuelve

1. Revisa la **bitácora** de la corrida y localiza las líneas no encontradas.
2. Verifica el **número de póliza** tal como aparece en el archivo (puede tener diferencias de formato, ceros, espacios).
3. Confirma que la póliza exista y que pertenezca a la **aseguradora** seleccionada en la corrida.
4. Si la póliza realmente no existe, hay que darla de alta o cargar la cartera antes de volver a importar.
5. Corrige el archivo y vuelve a procesar.

## Búsqueda de la póliza

- El sistema busca la póliza por **número** y **aseguradora** de la corrida.
- Si la aseguradora no coincide, o el número no existe, no se encuentra.

## Notas

- Las pólizas no encontradas **no detienen** el resto del proceso (tolerancia por fila).
- Se resuelven típicamente antes de reimportar o corrigiendo el número en el archivo.
