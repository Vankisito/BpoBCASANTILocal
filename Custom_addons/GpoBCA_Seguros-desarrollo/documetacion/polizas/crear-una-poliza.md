# Crear una póliza

El alta de una póliza se hace desde el menú **Pólizas** del área Gestión de Seguros.

## Pasos

1. Abre el menú **Pólizas**.
2. Haz clic en el botón **Nuevo** (accion general de creación, parte superior de la lista).
3. En el formulario de la póliza captura los datos obligatorios (ver *datos-generales*).
4. Completa las secciones del formulario:
   - Aseguradora y producto.
   - Contratante, asegurado, agente y promotoría.
   - Vigencia y periodicidad.
   - Primas e importes.
   - Coberturas y beneficiarios.
5. Guarda el registro con el botón **Guardar**.

Al guardar, la póliza queda en estado **Borrador**.

> **Importante:** mientras la póliza esté en **Borrador** se pueden editar todos sus campos. Al **confirmarla**, los campos principales quedan de solo lectura y el sistema genera el plan de recibos.

## Validaciones previas al poder crear

- La **aseguradora** debe existir en el catálogo (tipo BCA *Aseguradora*).
- El **producto** debe estar configurado para esa aseguradora y ramo.
- El **número de póliza** debe ser único por aseguradora.
- La **fecha de inicio** debe ser anterior a la **fecha de fin**.

## Notas

- El número de póliza se captura manualmente, no se genera solo.
- La **promotoría** se completa automáticamente al asignar el agente (es la promotoría actual del agente) y queda de solo lectura.
