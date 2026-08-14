# Pestaña "BCA Seguros" en el Módulo de Empleados — Propuesta

**Fecha:** agosto 2026
**Módulo:** `BCA_Seguros` (Odoo 19, Community)
**Autor:** Hábitat Digital

---

## 1. Contexto

Actualmente la información de agentes BCA (tipo de ente, promotoría, estado
de agente, claves por aseguradora, datos fiscales, referencias de pago
MetLife, etc.) vive en la pestaña **"BCA Seguros"** de la **ficha de
Contacto** (`res.partner`).

Los empleados se crean vinculados a su contacto agente mediante el campo
`work_contact_id` (`hr_applicant.py:530`): es decir, **cada empleado apunta a
su ficha BCA**. En Odoo 19 la ficha de empleado no muestra ese contacto ni la
pestaña BCA; el usuario debe ir a Contactos para verla.

**Solicitud:** mostrar la pestaña "BCA Seguros" en el módulo de Empleados.

**Restricción técnica relevante:** en Odoo, un campo `related` (espejo) **no
soporta campos One2many**. La lista "Claves por Aseguradora"
(`agente_aseguradora_ids`) no se puede duplicar con el mecanismo estándar de
espejo; requiere una solución específica (volcado read-only).

---

## 2. Ideas evaluadas

### Idea 1 — Pestaña espejo *editable* (copia completa del tab de contactos)

Se agregan a `hr.employee` campos `related` a `work_contact_id.bca_*` **con
edición habilitada** (los cambios escriben directo en el contacto). Se replica
la pestaña completa en la ficha de empleado, incluida la edición de claves por
aseguradora (con un workaround para el One2many).

| Pro | Contra |
|-----|--------|
| Tab completo e inline, sin cambiar de pantalla | Layout duplicado en 2 vistas que hay que mantener en sincronía |
| Edición directa desde Empleados | Riesgo de escrituras a mitad de camino (mitad en empleado, mitad en contacto) |
| Se ve y se edita en un solo lugar | La edición de claves One2many exige workaround frágil |

**Esfuerzo:** ~2–3 días. **Riesgo:** medio (mantenimiento y workaround).

### Idea 2 — Botón / navegación al contacto (mínima)

Un botón tipo "stat button" en la ficha de empleado que abre directamente la
ficha de Contacto del agente (donde ya está todo).

| Pro | Contra |
|-----|--------|
| Cero duplicación de datos | No es una pestaña inline |
| Fuente única de verdad garantizada | El usuario "sale" del empleado para ver/editar |
| Imposible desincronizar | Cambio visual pequeño |

**Esfuerzo:** ~0.5 día. **Riesgo:** nulo.

### Idea 3 — Pestaña espejo *solo lectura* + edición centralizada en Contactos **(ELEGIDA)**

Se replica la pestaña "BCA Seguros" en Empleados con todos los campos **en
solo lectura** (espejo del contacto) + botón **"Editar en Contactos"** que
abre la ficha del agente para cualquier modificación.

| Pro | Contra |
|-----|--------|
| Información visible inline en Empleados | No se edita desde Empleados |
| Cero riesgo de desincronización (el contacto sigue siendo única fuente de edición) | El usuario navega al contacto solo cuando quiere editar |
| Espejo 100% read-only: sin escrituras conflictivas | — |
| Las claves por aseguradora se muestran (read-only) vía volcado | — |

**Esfuerzo:** ~1 día. **Riesgo:** bajo.

---

## 3. Decisión

Se implementó la **Idea 3**: pestaña "BCA Seguros" read-only en Empleados,
visible para todos los empleados, con botón "Editar en Contactos" hacia la
ficha del agente. Razones:

- La fuente de verdad de la red BCA **ya es el contacto** (reclutamiento la
  alimenta vía automated actions). Duplicar la edición en Empleados crea dos
  puntos de escritura y riesgos de consistencia.
- La pestaña read-only entrega el valor de negocio (visibilidad sin salir de
  Empleados) con el menor costo de mantenimiento.
- Si en el futuro se quiere edición inline, migrar de Idea 3 → Idea 1 es
  incremental (quitar `readonly` y agregar el workaround del One2many).

---

## 4. Implementación (resumen técnico)

| Archivo | Cambio |
|---------|--------|
| `models/hr_employee.py` (nuevo) | `_inherit='hr.employee'` con campos espejo `related='work_contact_id.*'` read-only (prefijo `bca_` para no colisionar con `parent_id`/`country_id` nativos) + `bca_claves_aseguradora_ids` (Many2many computed read-only del One2many del contacto) + método `action_bca_open_contact()` |
| `views/hr_employee_views.xml` (nuevo) | Hereda `hr.view_employee_form`, inserta `<page name="bca_seguros">` con la misma estructura del tab de contactos, todo read-only + botón "Editar en Contactos" |
| `models/__init__.py` | Registra `hr_employee` |
| `__manifest__.py` | Agrega `hr` a `depends` y `views/hr_employee_views.xml` a `data` |
| `tests/test_views_xml.py` | Nuevo test `test_herencia_hr_employee` que valida el parseo de la vista heredada |

### Alcance de visibilidad

- La pestaña es **visible para todos los empleados** (los que no tengan
  contacto BCA verán los campos vacíos y el campo "Contacto Vinculado").
- Los grupos internos se ocultan según `bca_tipo` (Datos de Agente y Claves
  solo para agentes; Datos Fiscales solo para promotoría/agente), igual que en
  la ficha de contacto.

### Verificación

- Upgrade del módulo + suite de tests (`test_views_xml`, entre otros).
