# Roles y permisos de acceso

Roles y permisos

* [X]  Los permisos de BCA aparecen sin necesidad de tener el modo desarrollador activado
* [X]  Aparecen los roles Agente, Promotor, Lider, Director, Director comercial y operado
* [X]  Aparecen los roles de Reclutadora y Capital Humano en el apartado de reclutamiento

## Promotores

* [X]  Solo ven las pólizas que estén ligadas a su promotoría
* [X]  Solo ve los recibos que tiene ligada a su promotoría
* [X]  Su dashboard principal solo refleja los datos de sus recibos y pólizas
* [X]  Promotor no puede editar, crear recibos ni eliminarlos.
* [X]  Promotor no puede editar, creaer o eliminar pólizas
* [X]  El promotor no puede importar cobranza, portafolio o usar la funcionalidad de OCR.
* [X]  El promotor no puede acceder a la configuración, ni bitacoras de importación.

### Bugs promotores

* [ ]  Al ingresar a un recibo aparece el siguiente error : Sorry, ALMA VIERA (id=532) doesn't have 'read' access to: - Contact (res.partner)
* [ ]  Al intentar ingresar a una póliza aparece el siguiente error : You are not allowed to access 'Historial de Cambio de Agente en Póliza' (bca.poliza.cambio.agente) records.  This operation is allowed for the following groups: 	- BCA Seguros/Director BCA 	- BCA Seguros/Director Comercial BCA 	- BCA Seguros/Líder BCA 	- BCA Seguros/Operador BCA

## Creación de usuarios sin duplicarlos

* [X]  El campo de contacto existente aparece a la hora de crear un nuevo usuario
* [X]  El campo puede usarse a la hora de crear un usuario sin problemas.
* [X]  La funcionalidad permite crar contactos sin duplicarlos
* [X]  El usuario creado conserva su rol de bca(promotor, agente, etc)


## Vistas del modulo BCA

* [X]  Permite filtrar por promotores
* [X]  Permite agrupar por promotores
