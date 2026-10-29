# Reporte de estado de cartera

El reporte de **Estado de Cartera** muestra la situación de pago de las pólizas.

## Qué información contiene

- Lista de **pólizas activas** con su salud de pago.
- Dimensión de **pagado hasta** y **estatus de pago**.
- Identificación de pólizas **al corriente**, **por vencer** y **sin cobertura/vencidas**.

## Indicadores clave

| Indicador | Descripción |
|---|---|
| Al día | Pólizas activas con pago al día (pagado hasta >= hoy). |
| Por caer | Pólizas activas cuyo pago vence pronto (dentro del horizonte). |
| Sin cobertura | Pólizas sin pagos o con pago vencido. |

## Cómo se usa

- Para monitorear la **cartera activa** y su cobrabilidad.
- Para detectar pólizas que requieren seguimiento de cobranza.

## Origen de los datos

- Se calcula desde los **recibos pagados** (pagado hasta) y el **estatus de pago** de cada póliza.

## Notas

- El estatus de pago se actualiza con un **proceso diario** (cron) para que envejezca con el tiempo.
- Depende del **periodo de gracia** configurado.
