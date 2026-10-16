# Registrar pago manualmente

Un pago puede registrarse directamente sobre un recibo **pendiente**, sin archivo de cobranza.

## Pasos

1. Abre el **recibo** en estado Pendiente.
2. Completa los datos del pago:
   - **Fecha de pago** (obligatoria).
   - **Prima neta** (obligatoria, mayor que 0).
   - **Prima total** (opcional; por defecto igual a la neta).
   - **Recargo** (opcional).
   - **Conducto** (obligatorio en el flujo manual).
   - **Folio de endoso** (solo GMM, opcional).
3. Pulsa el botón **Registrar Pago**.

## Validaciones

- El recibo debe estar en **Pendiente**.
- La **fecha de pago** es obligatoria.
- La **prima neta** debe ser un valor positivo.
- Se respeta la **regla FIFO**: solo se puede pagar el pendiente más antiguo.
- En el flujo manual, el **conducto** es obligatorio.

## Qué ocurre

- El recibo pasa a **Pagado**.
- Se **calcula y congela** la PCA y el factor.
- Se registra la fotografía del **agente y promotoría** al momento del pago.
- Se actualiza el **Pagado Hasta** de la póliza.
- Al pagar el último pendiente de la anualidad, se genera la siguiente.

## Notas

- Si el recibo ya tiene un pago, no se puede volver a registrar (estado distinto de Pendiente).
- Para deshacer un pago manual, ver *cancelar-pago*.
