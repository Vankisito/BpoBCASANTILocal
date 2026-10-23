# Conductos sin coincidencia

Cuando el **conducto de pago** del archivo no coincide con ninguno configurado en el catálogo, el pago se registra como **advertencia**.

## Qué pasa

- El sistema busca el conducto por su **código de archivo** dentro del catálogo de conductos de la aseguradora.
- Si el código no coincide, **no se aborta** el proceso: el recibo se paga **con conducto vacío** y la fila se marca como **advertencia**.
- La advertencia queda registrada en la bitácora con el mensaje *"Conducto 'X' no encontrado en catálogo"*.

## Regla (R-COB-06)

> Un conducto sin coincidencia genera una **advertencia**, no un error: el pago se aplica de todos modos.

## Cómo se resuelve

1. Revisa las líneas **advertencia** de la bitácora.
2. Identifica el código de conducto que no coincidió.
3. Verifica el **código de archivo** en el catálogo de **Conductos** de esa aseguradora.
4. Si el código es válido pero no existe, se puede **configurar el conducto** en el catálogo.
5. En una corrida posterior con el conducto configurado, la advertencia desaparece.

## Impacto

- El pago queda **aplicado** (cuenta como aplicado para la cobranza).
- La PCA se sigue calculando y congelando.
- Solo queda la nota de advertencia por auditar.

## Notas

- Existe también el caso de **columna conducto vacía** (advertencia).
- El conductor vacío no impide cobrar.
