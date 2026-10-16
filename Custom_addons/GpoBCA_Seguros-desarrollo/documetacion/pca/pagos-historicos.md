# PCA de pagos históricos

La PCA de periodos anteriores se incorpora a los reportes a partir de los **recibos pagados** registrados en el sistema.

## Cómo se incorpora

- Cada **recibo pagado** conserva su PCA congelada con su **fecha de pago**.
- Los reportes de PCA (por agente, promotoría, consolidado) agregan esas PCA por dimensiones y periodos.
- El histórico se consulta filtrado por **fecha de pago** (rango de fechas).

## Pagos previos a la puesta en operación

- La **carga de cartera** permite importar el portafolio con su `pagado_hasta_inicial`.
- Se generan **solo los recibos posteriores** a esa fecha (no se crean recibos históricos pagados).
- Los pagos de periodos anteriores suelen incorporarse como recibos pagados ya congelados o vía carga, según el esquema de cada migración.

## Consulta

- Menú de **reportes de PCA** (ver sección Reportes):
  - rango de fechas de pago;
  - dimensión agente / promotoría / aseguradora / ramo.

## Notas

- El histórico es **inmutable**: la PCA de un recibo pagado no cambia.
- Un cambio de agente posterior no altera la PCA histórica.
- La elegibilidad (clave definitiva) se evalúa sobre el estado del puente; consulta *cuando-cuenta* para su matiz.
