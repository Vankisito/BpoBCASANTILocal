---
titulo: Guía de capacitación del módulo de empleados — BCA Seguros
subtitulo: Capacitación para Capital Humano
modulo: BCA_Seguros
version_modulo: 19.0.1.11.0
fecha: 2026-08-17
autor: Hábitat Digital
dirigido_a: Departamento de Capital Humano — Grupo BCA
---

# Guía de capacitación del módulo de empleados de BCA

## 1. Propósito de la capacitación

Esta guía tiene como objetivo orientar al equipo de Capital Humano en el manejo del módulo de empleados de BCA, con foco en los perfiles que operan en la organización:

- empleados internos de BCA
- agentes comerciales como trabajadores independientes

El propósito no es explicar de forma general cómo funciona Odoo, sino definir cómo debe utilizarse este módulo para registrar, validar y mantener la información de las personas que forman parte de la operación de BCA.

---

## 2. ¿Qué se administra en este módulo?

El módulo de empleados de BCA permite llevar el control de las personas que participan en la operación de la empresa, diferenciando claramente entre:

1. empleados internos
2. agentes comerciales

Esta diferencia es clave porque no todos los registros tienen el mismo tratamiento. Un empleado interno puede estar vinculado a una estructura de nómina y de organización interna; un agente, en cambio, opera como figura comercial independiente, sin recibir sueldo mensual, sino comisiones y premios por su desempeño.

---

## 3. Perfiles que maneja el módulo

### 3.1 Empleados internos de BCA

Son las personas que forman parte de la estructura operativa de la empresa, por ejemplo:

- recursos humanos
- finanzas
- administración
- operaciones
- soporte
- otras áreas corporativas

Para este tipo de personas, el módulo debe reflejar:

- datos personales básicos
- puesto o área funcional
- sede o ubicación de trabajo
- jefe o responsable directo
- relación laboral
- información necesaria para su control interno

### 3.2 Agentes comerciales de BCA

Son personas que participan en la operación comercial de la compañía, pero no se tratan como personal de nómina tradicional.

Sus características principales son:

- trabajan bajo una figura comercial
- no reciben sueldo fijo
- reciben comisiones por producción
- pueden recibir premios o reconocimientos por desempeño
- se registran como parte del esquema comercial y de habilitación

En este módulo, la gestión del agente debe verse como una figura comercial y de operación, no como un empleado de planta.

---

## 4. Diferencias clave entre empleados internos y agentes

| Tipo | Tratamiento principal | Forma de pago | Relación con la empresa | Uso principal del registro |
|---|---|---|---|---|
| Empleado interno | Personal de la organización | Nómina / salario | Relación laboral formal | Control interno y operativo |
| Agente | Figura comercial | Comisiones / premios | Relación comercial | Seguimiento comercial y habilitación |

### Regla de negocio importante

El agente no debe ser tratado como un empleado interno en términos de nómina. Su gestión se enfoca en:

- identidad y datos de registro
- vínculo comercial
- promotoría o estructura de operación
- habilitación y seguimiento
- comisiones y premios

---

## 5. Objetivos del módulo para Capital Humano

El módulo permite a Capital Humano:

- registrar correctamente a los empleados internos
- diferenciar claramente a los agentes comerciales
- mantener la información de contacto y organización actualizada
- apoyar el proceso de habilitación y seguimiento de agentes
- evitar confusiones entre personal interno y personal comercial
- contar con un registro ordenado para la operación de BCA

---

## 6. Qué debe revisar Capital Humano al momento del alta

### 6.1 Para un empleado interno

Antes de confirmar el alta, se debe verificar que estén completos los siguientes datos:

- nombre completo
- datos de identificación
- correo institucional
- teléfono de contacto
- área o departamento
- puesto
- sede o ubicación
- jefe directo
- información de soporte necesaria para la operación

### 6.2 Para un agente

Antes de confirmar el registro del agente, se debe verificar que estén completos los siguientes datos:

- nombre completo
- datos de identificación
- información de contacto
- vínculo comercial o promotoría
- estructura de operación asignada
- datos de habilitación requeridos por el proceso
- información de seguimiento para comisiones o premios

---

## 7. Flujo de trabajo recomendado para Capital Humano

### 7.1 Alta de un empleado interno

1. Identificar la persona y validar que corresponde a un empleado interno de BCA.
2. Registrar los datos básicos en el módulo.
3. Asignar el área, puesto y sede correspondiente.
4. Confirmar la estructura organizacional.
5. Revisar que la información esté completa antes de cerrar el registro.
6. Dar seguimiento a cambios posteriores si la persona cambia de puesto, sede o responsable.

### 7.2 Alta de un agente

1. Identificar que la persona corresponde a una figura comercial.
2. Registrar sus datos básicos en el módulo.
3. Asignar la estructura comercial correspondiente.
4. Verificar que la información de habilitación y seguimiento esté completa.
5. Mantener el registro actualizado para efectos comerciales y de control.
6. Asegurar que su manejo no se confunda con el de un empleado interno de nómina.

---

## 8. Reglas de negocio que debe conocer el equipo

### 8.1 Regla 1: no todo registro es un empleado interno

No todas las personas registradas en el módulo deben entenderse como personal de planta. Los agentes forman parte del esquema comercial y deben tratarse según esa lógica.

### 8.2 Regla 2: el agente no se maneja como personal de nómina

El agente no debe ser gestionado como un empleado con salario fijo. Su control está asociado a:

- producción
- comisiones
- premios
- seguimiento comercial

### 8.3 Regla 3: la información debe mantenerse actualizada

Cambios de puesto, sede, jefe, promotoría o área deben reflejarse de manera oportuna para que la información del módulo siga siendo útil y confiable.

### 8.4 Regla 4: la diferenciación entre perfiles evita errores operativos

Cuando el equipo distingue correctamente entre interno y agente, se reducen errores de clasificación, pagos, seguimiento y control.

---

## 9. Pestaña "BCA Seguros" en la ficha de Empleado

Desde la versión `19.0.1.11.0`, la ficha de cada empleado incluye una pestaña **"BCA Seguros"**
que muestra la información comercial del contacto vinculado. Esta pestaña es de **solo lectura**:
la fuente de verdad siempre es el contacto (`res.partner`), y la ficha de empleado solo proyecta
para consulta rápida.

### 9.1 Qué muestra la pestaña

La pestaña está organizada en las siguientes secciones:

#### Contacto Vinculado
- Muestra el contacto asociado al empleado (campo `work_contact_id`, solo lectura).
- Incluye el botón **"Editar en Contactos"** que abre directamente la ficha del contacto para
  realizar modificaciones.

#### Clasificación
- **Tipo BCA**: holding, aseguradora, promotoría o agente.
- **Promotoría (Contacto)**: la promotoría jerárquica del contacto.
- **Código Aseguradora**: código asignado por la aseguradora (solo si es tipo aseguradora).
- **Promotoría**: la promotoría del agente (solo si es tipo agente).
- **Es Contratante / Es Asegurado**: indicadores de roles de póliza.

#### Datos de Agente (solo agentes)
- **Estado Agente**: rollup del mejor estado alcanzado en cualquier aseguradora
  (Clave Definitiva > Clave de Arranque > Prospecto).

#### Claves por Aseguradora (solo agentes)
Lista que muestra las claves asignadas al agente por cada aseguradora:
- **Aseguradora**: nombre de la aseguradora.
- **Clave Agente**: número de clave asignado.
- **Estado**: badge con color según el estado (verde = Clave Definitiva, azul = Clave de Arranque,
  gris = Prospecto).
- **Fecha de Licencia**: fecha de emisión de la licencia.

#### Datos Demográficos
- Fecha de nacimiento, estado civil, género, CURP.

#### Referencias de Pago (MetLife)
- 8 referencias bancarias de cobro: prima básica (TRAD), prima médica, fondos variable/fijo
  (general, PPR, CPEA).

### 9.2 Cómo se edita la información

**Toda la información de la pestaña BCA Seguros es de solo lectura desde el empleado.**
Para modificar cualquier dato:

1. Hacer clic en el botón **"Editar en Contactos"**.
2. Se abrirá la ficha del contacto vinculado (`res.partner`).
3. Editar los campos necesarios en la pestaña "BCA Seguros" del contacto.
4. Guardar los cambios.
5. Los cambios se reflejan inmediatamente en la ficha del empleado al refrescar.

> **Nota importante**: La pestaña "BCA Seguros" del contacto (`res.partner`) sí permite edición
> directa (listas inline para claves, campos editables para clasificación y datos demográficos).
> La del empleado es solo consulta.

### 9.3 Regla clave

- **No intentar editar directamente en la pestaña del empleado** — todos los campos son de solo
  lectura.
- **Si falta información**, verificar que esté completa en el contacto vinculado.
- **Si un agente no tiene claves**, revisar que estén registradas en la pestaña "BCA Seguros" del
  contacto (sección "Claves por Aseguradora").

---

## 10. Qué debe observarse en la operación diaria

### En el caso de empleados internos

Revisar que:

- el registro se encuentre completo
- la ubicación y estructura estén correctas
- los cambios de puesto o área se reflejen en tiempo
- la información sea consistente con la realidad de la operación

### En el caso de agentes

Revisar que:

- el agente esté correctamente identificado
- su proceso comercial y de habilitación esté alineado
- la información de operación y seguimiento esté completa
- los datos necesarios para comisiones o premios estén disponibles

---

## 11. Errores comunes que conviene evitar

- registrar a un agente como si fuera un empleado interno de planta
- omitir datos clave de identificación o operación
- no distinguir entre personal de nómina y personal comercial
- no actualizar cambios de área, sede o estructura comercial
- dejar registros incompletos que luego complican el seguimiento

---

## 12. Checklist de cierre para Capital Humano

Antes de cerrar un registro, confirmar:

- [ ] los datos básicos están completos
- [ ] la persona está correctamente clasificada como interno o agente
- [ ] la estructura organizacional o comercial fue asignada
- [ ] los datos de seguimiento están disponibles
- [ ] la información es consistente con la operación real de BCA

---

## 13. Resumen para la capacitación

La gestión del módulo de empleados en BCA debe entenderse como una herramienta para distinguir dos realidades distintas:

- el personal interno de la organización
- los agentes comerciales que operan con un esquema diferente

El éxito de la operación depende de que Capital Humano mantenga registros claros, completos y diferenciados, para que la información refleje correctamente la estructura real de la empresa.

---

## 14. Sugerencia de cierre de capacitación

Al finalizar la sesión, el equipo debe poder responder con claridad:

- ¿cuándo un registro corresponde a un empleado interno?
- ¿cuándo corresponde a un agente?
- ¿qué información debe revisarse en cada caso?
- ¿por qué es importante diferenciar ambos perfiles?
- ¿qué impacto tiene una clasificación incorrecta en la operación de BCA?
