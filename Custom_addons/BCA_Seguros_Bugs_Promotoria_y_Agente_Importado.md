# BCA_Seguros — Reporte de bugs: Usuarios promotores y Agente importado sin Promotoría

| Campo | Valor |
|---|---|
| **Módulo** | `BCA_Seguros` · Odoo 19 Community · código revisado: **19.0.1.16.2** (copia local `GpoBCA_Seguros-desarrollo`) · versión en staging: *No confirmado* |
| **Entorno de la prueba** | Staging — `bca-staging.habitatdigital.net` |
| **Área** | QA — Hábitat Digital |
| **Elaboró** | Yaziel (QA) |
| **Fecha** | 09 de octubre de 2026 |
| **Bugs** | BUG-025 y BUG-026 (*propuestos. En `Specs/Bugs.md` el último registrado es BUG-023; BUG-024 está propuesto en la Guía de Acceso Promotoría*) |

---

## Resumen

| ID | Título | Tipo | Prioridad propuesta | Estado |
|---|---|---|---|---|
| BUG-025 | El usuario promotor no aparece en *Usuarios promotores* de la Promotoría | Lógica | 🟠 Alta | Abierto (causa por confirmar en staging) |
| BUG-026 | Agente sin Promotoría queda bloqueado: no se puede asignar ni directo ni con "Cambiar Promotoría" | Lógica | 🔴 Crítica | Abierto (causa confirmada en código) |

> Las prioridades son propuesta de QA. Validar con Dev/PM.

---

## BUG-025 — El usuario promotor no aparece en "Usuarios promotores"

| Campo | Valor |
|---|---|
| **Fecha** | 2026-10-09 |
| **Vista / Origen** | Contactos › Promotoría (Tipo BCA = Promotoría) › pestaña *BCA Seguros* › *Clasificación* › *Usuarios promotores* |
| **Tipo** | Lógica |
| **Prioridad** | 🟠 Alta (bloquea la validación del alta de promotorías del Manual) |
| **Estado** | Abierto: el código local debería mostrarlo; hay que confirmar la causa en staging |
| **Traceback** | No. Bug silencioso |

### Descripción

Siguiendo el guion *Promotoría empresa* (`Specs/Manual_Alta_Promotorias_Usuarios_BCA.md`, Paso 6), se crea el contacto persona **PersonaQAPromotor** ligado a la Promotoría empresa, sin Tipo BCA, y un usuario interno con rol **Promotor BCA** sobre ese contacto. El usuario se crea bien y queda ligado al contacto correcto, pero **no aparece** en *Usuarios promotores* de la Promotoría.

### Resultado del guion de prueba

| # | Paso | Resultado |
|---|---|---|
| 1 | Crear contacto empresa con `Tipo BCA = Promotoría` | ✅ |
| 2 | Activar `Es una empresa` | ✅ |
| 3 | Asignar Holding | ✅ |
| 4 | Guardar Promotoría | ✅ |
| 5 | Crear contacto persona del promotor (**PersonaQAPromotor**) | ✅ |
| 6 | Asignar `Empresa / Pertenece a` = la Promotoría empresa | ✅ |
| 7 | No asignar `Tipo BCA` al contacto persona | ✅ |
| 8 | Crear usuario interno | ✅ |
| 9 | En `Contacto existente`, seleccionar el contacto persona | ✅ |
| 10 | Asignar `BCA Seguros → Rol BCA Seguros → Promotor BCA` | ✅ |
| 11 | Guardar usuario | ✅ |
| 12 | Confirmar que no se creó contacto duplicado | ✅ |
| 13 | Confirmar que `Contacto relacionado` es el contacto persona | ✅ |
| 14 | Abrir Promotoría → `BCA Seguros` → `Usuarios promotores` | ❌ |
| 15 | Confirmar que aparece el usuario | ❌ **No aparece** |

**Esperado (según el Manual, Paso 6):** aparece el usuario promotor. La lista incluye los usuarios ligados directamente a la Promotoría y los usuarios cuyos contactos hijos pertenecen a ella.
**Actual:** el usuario no aparece.

### Revisión de código (versión local 19.0.1.16.2)

| Punto revisado | Archivo | Qué hace |
|---|---|---|
| Cálculo del campo | `models/res_partner.py:282` | `user_ids \| child_ids.mapped('user_ids')`: incluye los usuarios de los contactos hijos |
| Filtros | mismo método | No filtra por Tipo BCA ni por grupo. Un contacto persona **sin** Tipo BCA sí cuenta |
| Almacenado | `res_partner.py:205` | No es `store=True`: se calcula al abrir el formulario, no hay problema de recálculo |
| Visibilidad | `views/res_partner_views.xml:36` | Solo lo ven *Director Comercial BCA* o *Director BCA* |
| Prueba automatizada | `tests/test_promotor_security.py` | `test_promotoria_user_ids_are_source_of_assignment` cubre este mismo caso (usuario con contacto hijo de la promotoría) |

**Conclusión:** con el código local, el escenario del guion **debería funcionar**. Se descartan las hipótesis iniciales (que el cálculo ignore a los hijos, que exija Tipo BCA o que no se recalcule). La falla en staging apunta a una de estas causas, que hay que verificar:

| # | Causa posible | Cómo verificar |
|---|---|---|
| C1 | Staging tiene una versión anterior a la que incluye este cálculo | *Aplicaciones* › BCA_Seguros › versión instalada. Comparar con 19.0.1.16.2 |
| C2 | El contacto persona quedó ligado a **otro** registro (otra Promotoría con nombre parecido, o el Holding) | Abrir PersonaQAPromotor y entrar con clic al campo *Empresa*: debe abrir la misma Promotoría que se revisó |
| C3 | El usuario que revisa no tiene Director Comercial ni Director, y el campo no se muestra | *Poco probable*: en la prueba de BUG-026 el mismo administrador sí ve el botón *Cambiar Promotoría*, que pide los mismos grupos. Confirmar que fue el mismo usuario |

### Impacto

- El paso de validación del Manual de alta no se puede completar.
- Según la Guía de Acceso Promotoría, la visibilidad de la red del promotor (BUG-024) depende de esta liga: si en staging falla C1 o C2, el promotor tampoco verá su cartera.

### Evidencia a adjuntar

- [ ] Captura de la Promotoría con *Usuarios promotores* (vacío o sin el campo).
- [ ] Captura de PersonaQAPromotor mostrando *Empresa* = la Promotoría.
- [ ] Captura de la versión instalada en *Aplicaciones*.

---

## BUG-026 — Agente sin Promotoría queda bloqueado

| Campo | Valor |
|---|---|
| **Fecha** | 2026-10-09 |
| **Vista / Origen** | Contactos › Agente (Tipo BCA = Agente) › campo *Empresa* y botón *Cambiar Promotoría* |
| **Tipo** | Lógica |
| **Prioridad** | 🔴 Crítica (el registro no se puede guardar ni corregir desde la interfaz) |
| **Estado** | Abierto: causa confirmada en código |
| **Traceback** | No. Mensaje de validación (`UserError`) |
| **Registro de ejemplo** | **LAURA ORENCIO ORTEGA** (55 pólizas, 237 recibos, Estado Agente = Prospecto), abierto desde la póliza 1460031 |

### Descripción

Un Agente que existe **sin promotoría** no se puede corregir por ninguna vía:

1. El formulario no guarda: *Pertenece a* es obligatoria para agentes y aparece *"Faltan algunos campos obligatorios"*.
2. Si se captura la *Empresa* en el campo superior del formulario, al guardar aparece:
   > **Operación no válida** — La Promotoría de "LAURA ORENCIO ORTEGA" no se puede cambiar directamente. Use "Cambiar Promotoría" para dejar auditoría.
3. El botón **Cambiar Promotoría** no abre, porque Odoo intenta guardar el formulario antes de ejecutarlo y el campo obligatorio vacío lo impide.

### Pasos para reproducir

1. Abrir un agente sin Promotoría (ejemplo: LAURA ORENCIO ORTEGA).
2. **Vía A:** capturar *Empresa* y guardar → *Operación no válida*.
3. Descartar cambios.
4. **Vía B:** clic en **Cambiar Promotoría** → *Faltan algunos campos obligatorios*.

**Esperado:** la **primera** asignación de Promotoría (de vacío a un valor) se puede hacer y queda auditada.
**Actual:** ninguna vía funciona.

### Causa raíz (confirmada en código 19.0.1.16.2)

Hay cuatro bloqueos y cualquiera de ellos basta para impedir la corrección:

| # | Bloqueo | Archivo | Detalle |
|---|---|---|---|
| 1 | Protección de `write()` | `models/res_partner.py:456` | Compara `nuevo_parent_id != rec.parent_id.id`. Si el agente no tiene promotoría, el valor anterior es vacío, así que **cualquier** asignación cuenta como "cambio" y se rechaza. Es el mensaje de la captura |
| 2 | Campo *Pertenece a* en la pestaña | `views/res_partner_views.xml:28-29` | Es de **solo lectura** para un agente ya guardado (`readonly="id and …"`) y al mismo tiempo **obligatorio**. Ahí no se puede capturar y por eso el formulario no guarda |
| 3 | Botón *Cambiar Promotoría* | `views/res_partner_views.xml:54` | Es `type="object"`: Odoo guarda el formulario antes de ejecutarlo, y el bloqueo 2 lo impide |
| 4 | El wizard no admite primera asignación | `wizards/cambio_promotoria.py:79` y `models/res_partner.py:369` | Aunque abriera, rechaza agentes sin promotoría: *"El Agente no tiene una Promotoría actual válida"*. El flujo auditado se diseñó solo para **mover** agentes entre promotorías, no para asignar la primera |

### ¿Cómo existe un agente sin promotoría?

`_check_jerarquia` (`res_partner.py:465`) exige que todo agente pertenezca a una Promotoría al crearlo o modificarlo. Por eso un agente así no debería poder existir:

- *Cargar Portafolio* (`wizards/carga_portafolio.py:895`) **no crea agentes**: los busca por clave y falla si la clave no está registrada.
- Reclutamiento (`hr_applicant.py`) crea el agente **con** la promotoría destino.

Lo más probable es que el registro venga de una carga o migración que **no pasó por esta validación**: datos anteriores a la regla, una importación nativa o un script. *No confirmado*: hay que identificar el wizard o proceso exacto.

### Propuesta (sugerencia de QA; la decisión es de Desarrollo)

1. **Permitir la primera asignación** en el flujo auditado: que *Cambiar Promotoría* (o una acción "Asignar Promotoría") acepte agentes sin promotoría y registre la auditoría con *Promotoría anterior* vacía.
2. Que el botón funcione aunque el formulario tenga el campo obligatorio vacío (por ejemplo, una acción desde la lista de agentes o una acción de servidor).
3. **Saneamiento de datos:** listar los agentes sin promotoría y asignarlos con el flujo corregido.
4. Identificar y cerrar el camino por el que entraron agentes sin promotoría.

### Impacto

- El agente no se puede editar en absoluto (ni la promotoría ni otros datos), porque el formulario no guarda.
- Sus 55 pólizas no quedan bajo ninguna promotoría: afecta la visibilidad por promotoría (BUG-024) y los reportes por red.
- No hay solución desde la interfaz; corregir los datos actuales requiere intervención de Desarrollo.

### Evidencia

- [x] Captura 1: formulario del agente con *Empresa* y *Pertenece a* en rojo y aviso *"Faltan algunos campos obligatorios"*.
- [x] Captura 2: diálogo *Operación no válida* al capturar la Empresa directamente.
- [ ] Captura del intento con el botón *Cambiar Promotoría*.

### Pendientes de verificar

- [ ] **Origen exacto** del agente: ¿qué wizard o proceso lo creó? *(No confirmado)*
- [ ] Cuántos agentes están igual: *Configuración › Agentes*, filtrar *Promotoría* vacía. *(No confirmado)*
- [ ] Observación secundaria: el agente tiene 55 pólizas y *Estado Agente* = **Prospecto**. El estado se calcula desde las claves por aseguradora: si no tiene claves, queda en Prospecto. Revisar si tiene claves registradas. *(No confirmado; no se reporta como bug por ahora)*

---

## Casos de prueba para re-test

| ID | Caso | Resultado esperado |
|---|---|---|
| TC-025-01 | Promotor ligado por contacto persona hijo | Aparece en *Usuarios promotores* |
| TC-025-02 | Contacto persona sin `Tipo BCA` | El usuario aparece igual |
| TC-025-03 | Usuario sin Director Comercial / Director abre la Promotoría | No ve el campo (comportamiento esperado) |
| TC-026-01 | Primera asignación a agente sin promotoría | Se asigna y queda registro en la auditoría de cambios de promotoría |
| TC-026-02 | Cambio directo A → B con promotoría ya asignada | Sigue bloqueado con *Operación no válida* (la protección se mantiene) |
| TC-026-03 | Cambio A → B con *Cambiar Promotoría* | Funciona y queda auditado |
| TC-026-04 | Usuario sin Director Comercial / Director | No ve el botón ni puede asignar |
| TC-026-05 | Búsqueda de agentes sin promotoría después del saneamiento | 0 resultados |

---

## Mensaje para el equipo (Teams)

```
Equipo, levanté dos bugs en BCA Seguros (BCA_Seguros_Bugs_Promotoria_y_Agente_Importado):

BUG-026 (Crítica): un agente sin promotoría no se puede corregir. El write()
de res.partner (línea 456) trata la primera asignación como "cambio" y la
rechaza; "Pertenece a" es readonly y required para agentes guardados, así que
el form no guarda y el botón "Cambiar Promotoría" no abre; y el wizard rechaza
agentes sin promotoría actual (cambio_promotoria.py:79). Ejemplo: LAURA
ORENCIO ORTEGA (55 pólizas). Propuesta: permitir la primera asignación auditada
y sanear los agentes sin promotoría. Falta confirmar por dónde entraron, porque
_check_jerarquia no debería permitirlos.

BUG-025 (Alta): en staging el usuario Promotor BCA no aparece en "Usuarios
promotores". En el código local (19.0.1.16.2) el cálculo sí incluye los
contactos hijos y hay test que lo cubre, así que sospecho una versión distinta
en staging. ¿Me confirman qué versión está desplegada?
```
