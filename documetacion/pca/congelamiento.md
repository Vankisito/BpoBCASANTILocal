# Congelamiento de la PCA

Cuando un recibo se paga, su **PCA** y su **factor** quedan **congelados** e inmutables.

## Qué significa "congelar"

- El valor de PCA calculado al momento del pago queda fijado.
- También el **factor aplicado** y el **motivo de exclusión**.
- Estos valores **no se pueden editar** después.

## Cuándo ocurre

- Al **registrar el pago** del recibo (manual o por archivo), en el mismo momento en que el recibo pasa a **Pagado**.

## Protección

- El sistema **bloquea** la edición de los campos de PCA (`pca_aplicada`, `factor_aplicado`, `pca_currency_id`) en recibo pagados.
- Solo se permite modificarlos con autorización interna (superusuario) o al **cancelar el pago** autorizadamente, que revierte el recibo a pendiente.

## Qué se conserva (fotografía inmutable)

Además de la PCA, al pagar se conserva:

- **Agente** al momento del pago.
- **Promotoría** al momento del pago.
- Fecha de pago, conducto, prima.

## Implicación en reportes

- Los reportes de PCA usan la **PCA congelada** del recibo.
- Si el agente cambia después, la PCA reportada no se mueve (sigue al agente de la fotografía).

## Notas

- Para corregir una PCA, se debe **cancelar el pago** (rol autorizado) y volver a registrarlo.
- El congelamiento garantiza la integridad financiera del histórico.
