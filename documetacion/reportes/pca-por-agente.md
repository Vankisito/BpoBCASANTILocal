# PCA por agente

El reporte de **PCA por Agente** desglosa la producción acreditada a cada agente.

## Cómo consultarlo

- Menú **Reportes** → **PCA por Agente** del área Gestión de Seguros.

## Qué muestra

- Grano: un **recibo pagado** por fila.
- Dimensiones: **agente**, promotoría, aseguradora, producto, ramo, **fecha de pago**.
- Métricas: **PCA** (en MXN) y **factor** aplicado.

## Regla de filtrado

- Solo incluye recibos **pagados** cuyos agentes estén en **Clave Definitiva** en la aseguradora de la póliza.
- Usa la **fotografía del recibo** (agente al momento del pago), no el agente actual de la póliza.

## Uso

- Ver cuánta PCA acumula cada agente en un periodo.
- Analizar la producción por aseguradora, ramo o promotoría.

## Formato

- Vista por defecto **pivot**, con opciones de gráfica y lista.
- Filtra por rango de **fecha de pago**, agente, aseguradora, ramo, etc.

## Notas

- Un agente en Clave de Arranque **no aparece** en este reporte aunque tenga recibos pagados (ver sección PCA → *cuando-cuenta*).
