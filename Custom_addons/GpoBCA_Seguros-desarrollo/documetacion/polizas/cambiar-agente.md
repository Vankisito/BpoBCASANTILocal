# Cambiar agente

La reasignación del agente de una póliza se hace mediante la acción **Cambiar agente**, que deja un historial auditable.

## Pasos

1. Abre la póliza.
2. Usa la acción/botón **Cambiar agente**.
3. Selecciona el **nuevo agente** (debe ser un contacto de tipo *Agente*).
4. Captura el **motivo** de la reasignación.
5. Confirma.

## Reglas y validaciones

- El nuevo agente debe ser de tipo **Agente**. Si se elige otro tipo de contacto, el sistema lo rechaza.
- El cambio queda registrado en el **historial de cambios de agente** (inmutable): agente anterior, agente nuevo, promotoría anterior, promotoría nueva y motivo.
- La **promotoría** de la póliza se actualiza con la promotoría del nuevo agente.

## Efecto en PCA / comisiones

- Los **pagos ya registrados** conservan al agente que estaba al momento del pago (fotografía inmutable en el recibo).
- Por tanto, **la PCA ya reportada no se mueve** al nuevo agente: sigue atribuida al agente original del pago.
- Solo la cobranza **posterior** al cambio se atribuye al nuevo agente.

## Permisos requeridos

Históricamente la reasignación está restringida a roles de gestión (Director / Director Comercial según la configuración del perfil). Verifica los permisos de tú perfil antes de operar.

## Notas

- El cambio agrega una entrada al contador **Cambios de Agente** de la póliza, consultable desde el formulario.
