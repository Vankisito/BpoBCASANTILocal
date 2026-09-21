# Bitácora de Bugs — Módulo BCA_Seguros

Registro de defectos detectados en el módulo `BCA_Seguros` (Odoo 19 Community).
Cada bug tiene un ID único e **inmutable** (`BUG-XXX`); al resolverse, el bug se
mueve de *Encontrados* a *Resueltos* conservando su ID.

## Leyenda

**Prioridad** (orden sugerido de atención):
- 🔴 **Crítica** — bloquea operación / pérdida de datos / cálculo incorrecto de dinero.
- 🟠 **Alta** — funcionalidad principal rota o ausente; sin workaround razonable.
- 🟡 **Media** — funciona con fricción o hay workaround; afecta la experiencia.
- ⚪ **Baja** — cosmético / configuración / menor.

**Tipo:** `Lógica` (negocio) · `UI/UX` · `Datos` · `Config` · `Seguridad`

**Estado:** `Abierto` · `En progreso` · `Resuelto` · `Pendiente-config` (requiere ajuste en la instancia, no código)

## Cómo registrar un bug nuevo

Agregar una fila en *Bugs Encontrados* con el próximo `BUG-XXX` libre, fecha,
vista/origen, descripción, tipo y prioridad. Si tiene pasos de reproducción no
obvios, añadir un bloque en *Detalle de bugs abiertos*. Al resolverlo, moverlo a
*Bugs Resueltos* con el commit y la fecha.

---

## Bugs Encontrados (Abiertos)

| ID | Fecha | Vista / Origen | Descripción | Tipo | Prioridad | Estado |
|----|-------|----------------|-------------|------|-----------|--------|
| BUG-012 | 2026-05-27 | Recibo (form), Póliza (pestaña Recibos), Contactos | Las fechas (Cobertura Desde/Hasta, Fecha de Pago) no se muestran en formato día/mes/año. | Config | ⚪ Baja | Pendiente-config |
| BUG-013 | 2026-05-27 | Póliza → form → pestaña "Recibos" | Al abrir un recibo desde la pestaña se muestra un popup con botón "Registrar Pago", pero la sección "Datos del Pago" no es editable en ese diálogo, por lo que el botón no tiene funcionalidad real. | UI/UX | 🟡 Media | Abierto |
| BUG-015 | 2026-06-05 | Datos: `bca.poliza.coaseguro` vs `bca.factor.pca.coaseguro_min` | Desajuste de unidades de coaseguro: la póliza lo guarda como fracción (`0.10`=10%) y el seed de factores GMM como puntos porcentuales (`coaseguro_min=10.0`). El calculador de PCA (E7) lo normaliza, pero la inconsistencia de esquema persiste y puede confundir captura/reportes. | Datos | 🟡 Media | Abierto |
| BUG-018 | 2026-08-07 | Póliza → lista → agrupar por Promotoría | `promotoria_id` no almacenado provocaba `ValueError` en `read_group`; además la jerarquía de red no tenía flujo auditado para cambios directos de `parent_id`. | Lógica | 🟡 Media | Resuelto |
| BUG-023 | 2026-09-09 | Recibo (form) → Cancelar Pago | `prima_total_pagada` no se limpia a 0 al cancelar un pago desde el form de recibo. En tableros y PCA sí se cancela correctamente. | Lógica | 🟡 Media | Resuelto |

### Detalle de bugs abiertos (cont.)

**BUG-015 — Unidades inconsistentes de `coaseguro`**
- *Causa:* `bca.poliza.coaseguro` (Float) documenta "0.05 = 5%" (fracción), pero los registros de `bca.factor.pca` (campos `coaseguro_min`/`coaseguro_max`) se sembraron en puntos porcentuales (`10.0` = 10%).
- *Mitigación actual (E7):* `CalculadorPCAMetLife._evaluar_exclusiones` / `_buscar_factor` normalizan con `coaseguro_pct = poliza.coaseguro * 100` antes de comparar contra el factor.
- *Solución propuesta (a futuro):* unificar a una sola escala — preferible que ambos usen fracción (`0.10`) o ambos puntos (`10.0`), ajustando seed + help + UI + el calculador en una sola pasada, con migración de datos para los factores existentes (`noupdate="1"`).

### Detalle de bugs abiertos

**BUG-012 — Formato de fecha DD/MM/YYYY**
- *Causa:* Odoo renderiza los campos `Date` según el `date_format` del idioma activo; no existe override por campo en la vista.
- *Solución propuesta (configuración, no código):* Ajustes → Traducciones → Idiomas → Español (México) con `date_format = %d/%m/%Y`, y asignar ese idioma a los usuarios/empresa. Afecta a todas las fechas del sistema (deseable para despliegue MX).

**BUG-013 — "Registrar Pago" inutilizable desde la pestaña Recibos de la póliza**
- *Pasos para reproducir:* Póliza activa → pestaña "Recibos" → clic en una fila de recibo → se abre el form del recibo en diálogo.
- *Comportamiento actual:* El diálogo se abre en modo solo lectura (la pestaña declara el one2many `recibo_ids` como `readonly="1"`), por lo que "Datos del Pago" (fecha_pago, conducto) no se puede completar y "Registrar Pago" falla o no hace nada útil.
- *Comportamiento esperado:* O bien no mostrar "Registrar Pago" en ese contexto, o abrir el recibo en su formulario editable para poder cobrarlo.
- *Soluciones candidatas (a evaluar):* (a) ocultar el botón cuando el form se abre embebido/diálogo vía un flag de contexto; (b) que el clic en la fila navegue al form completo editable del recibo (no diálogo); (c) registrar el pago siempre desde el menú **Recibos** (workaround actual).

---

## Bugs Resueltos

Resuelto el **2026-08-24** (versión `19.0.1.11.1`):

| ID | Vista / Origen | Descripción | Tipo | Prioridad | Solución | Commit |
|----|----------------|-------------|------|-----------|----------|--------|
| BUG-022 | BCA Seguros → Reportes → submenú "SIC Reclutamiento" | El submenú SIC Reclutamiento aparecía en el apartado Reportes pese a no estar operativo para producción; se solicitó ocultarlo para TODOS los usuarios sin eliminarlo (podría reutilizarse a futuro). | UI/UX / Config | 🟡 Media | Atributo `active="False"` en el `menuitem menu_bca_sic_reclutamiento` (`views/menu.xml`). El registro `ir.ui.menu` y la acción `action_sic_reclutamiento` permanecen intactos en BD (los tests de reclutamiento siguen usando la acción). Reactivación: quitar `active="False"` + `-u BCA_Seguros`. Ver D-22. | pendiente |

Resuelto el **2026-08-18**:

| ID | Vista / Origen | Descripción | Tipo | Prioridad | Solución | Commit |
|----|----------------|-------------|------|-----------|----------|--------|
| BUG-020 | Contactos (form), Empleados (form) → pestaña BCA Seguros | Reclutadora BCA y Capital Humano BCA no podían visualizar la ficha de contacto ni de empleado: el campo "Clave de agente por aseguradora" (`agente_aseguradora_ids` / `bca_claves_aseguradora_ids`) no cargaba por falta de ACL en `res.partner.agente.aseguradora` para esos grupos. | Seguridad | 🟠 Alta | (1) 2 ACL rows (solo lectura) en `ir.model.access.csv` para `group_bca_reclutadora` y `group_bca_capital_humano` sobre `model_res_partner_agente_aseguradora`. (2) 2 record rules `[(1,'=',1)]` (lectura global) en `record_rules.xml` para ambos grupos — patrón A3: grupos fuera de la cadena acumulativa de `implied_ids` requieren rule explícita. | pendiente |
| BUG-021 | Contactos (form) → smart buttons Pólizas/Recibos | Reclutadora BCA y Capital Humano BCA no podían abrir fichas de contacto que tengan rol de póliza/agente: los smart buttons de Pólizas y Recibos intentaban cargar `bca.poliza`/`bca.recibo` sin ACL para esos grupos, lanzando `AccessError`. | Seguridad | 🟠 Alta | Atributo `groups` en los 2 botones smart (`res_partner_views.xml`) restringiéndolos a los 5 grupos de la cadena BCA. Reclutadora/Capital Humano no necesitan ver pólizas desde contactos. | pendiente |

Resuelto el **2026-08-12** (versión `19.0.1.11.0`):

| ID | Vista / Origen | Descripción | Tipo | Prioridad | Solución | Commit |
|----|----------------|-------------|------|-----------|----------|--------|
| BUG-019 | Póliza, Recibo, Reportes PCA, Dashboard, búsquedas (contactos Agente/Promotoría) | Los campos **Agente** y **Promotoría** mostraban "Contacto, Empresa": el nombre del contacto junto al de la promotoría/holding (ej. `Juan Pérez Hernández, Agencia BCA Monterrey`). Odoo nativo antepone la empresa en `_get_complete_name`; el cliente pidió mostrar solo el nombre del contacto. Afectaba listas de pólizas/recibos, reportes PCA, dashboard y cuadros de búsqueda. | UI/UX | 🟡 Media | Override `_compute_display_name` en `res.partner` que aplica la key nativa `partner_display_name_hide_company` para `bca_tipo` agente/promotoria. La relación `parent_id` (base de comisiones y reportes) permanece intacta; el resto de contactos conserva el formato nativo. Verificado en `bca_clean` (tests + smoke test live). | `c06ca02` |

Resuelto el **2026-08-10** (versión `19.0.1.10.0`):

| ID | Vista / Origen | Descripción | Tipo | Prioridad | Solución | Commit |
|----|----------------|-------------|------|-----------|----------|--------|
| BUG-018 | Póliza → lista → agrupar por Promotoría | `promotoria_id` no almacenado provocaba `ValueError` en `read_group`; además la jerarquía de red no tenía flujo auditado para cambios directos de `parent_id`. | Lógica | 🟡 Media | `bca.poliza.promotoria_id` y `res.partner.bca_promotoria_id` almacenados/indexados; gobernanza de red y transferencia auditada. | Pendiente |

Resuelto el **2026-07-13** (rama `desarrollo`; **sin cambio de código** — solo documentación de referencia):

| ID | Vista / Origen | Descripción | Tipo | Prioridad | Solución | Commit |
|----|----------------|-------------|------|-----------|----------|--------|
| BUG-017 | Reclutamiento (Etapa 12) — puestos internos | Divergencia **documentación ↔ código**, no defecto de código. El QA Manual (v19.0.1.7.4) describía una etapa BCA "Contratado (Alta Interna)" (retirada en 19.0.1.7.7, D-20) y que el empleado se creaba en "Cédula Emitida" (pre-D-21). En QA se interpretó que "Contrato firmado" exigía Sede/Promotoría/Clave para internos y que no había forma de dar de alta empleados internos. **Realidad verificada:** las constraints comerciales solo aplican a `job_reclutamiento_agente`/`job_captacion_promotoria` (test `test_job_interno_nativo_no_crea_puente_ni_agente` pasa); los internos usan el **embudo nativo** y se dan de alta con el **botón manual "Create Employee"**; el empleado del agente comercial se crea en **"Clave Definitiva"** (seq 13). No hay puestos internos sembrados, por lo que un candidato de prueba bajo un puesto comercial exhibe la exigencia correcta del embudo. | Datos/Doc | 🟡 Media | Reconciliación de `QA_Manual_Etapa12_Reclutamiento.md` a la conducta vigente D-21 (etapa "Alta Interna" retirada; empleado en "Clave Definitiva"; interno = embudo nativo + botón manual). **Decisión:** NO se automatiza el alta interna; se conserva el botón manual nativo. | — (docs) |

Resuelto el **2026-06-05** (rama `desarrollo`; deploy a sandbox `sandbox_bca1` confirmado sin error):

| ID | Vista / Origen | Descripción | Tipo | Prioridad | Solución | Commit |
|----|----------------|-------------|------|-----------|----------|--------|
| BUG-014 | Contactos (form, Agente, pestaña BCA Seguros) | Al abrir un Agente, la pestaña BCA crasheaba con `OwlError → TypeError: Cannot read properties of undefined (reading '1')` en `SelectionField`. Causa: registros viejos con `bca_estado_agente`/`estado='con_licencia'`, valor eliminado del `Selection` al pasar a la nomenclatura de 3 estados (D-07). No afectaba a promotorías (no renderizan esos campos). | Datos | 🔴 Crítica | Migración `migrations/19.0.1.1.0/post-migrate.py`: mapea `con_licencia→clave_definitiva` en el puente, sanea el rollup del partner y lo recalcula desde el puente. Bump de manifest a `19.0.1.1.0`. | `0b08f3b` |
| BUG-016 | `bca.recibo.action_registrar_pago` → `_calcular_pca` (calculador MetLife) | La PCA quedaba congelada en **0** al pagar todo recibo: el cálculo corría ANTES del write que asigna `fecha_pago`, así que el calculador leía `recibo.fecha_pago=False` y el filtro `vigencia_desde <= False` no encontraba el factor vigente (`'Sin factor PCA vigente'`). Bug latente en `recibo.py` desde la E7; las 6 pruebas de `test_pca_metlife` que esperan factor ≠ 0 lo destaparon en el primer `-u` honesto sobre `sandbox_bca1`. | Lógica | 🔴 Crítica | Fijar `rec.fecha_pago = vals['fecha_pago']` **antes** de `_calcular_pca()` en `action_registrar_pago`. Validado en sandbox (`_calcular_pca` → `(12000.0, 1.0, '')`); suite completa **135 tests, 0 failures**. | `38736b7` |

Resuelto el **2026-09-09**:

| ID | Vista / Origen | Descripción | Tipo | Prioridad | Solución | Commit |
|----|----------------|-------------|------|-----------|----------|--------|
| BUG-023 | Recibo (form) → Cancelar Pago | `prima_total_pagada` no se reseteaba a 0 al cancelar un pago desde el form de recibo. Los campos de PCA (`pca_aplicada`, `factor_aplicado`) y otros datos del pago sí se limpiaban, pero `prima_total_pagada` quedaba con el valor anterior. | Lógica | 🟡 Media | Agregar `'prima_total_pagada': 0.0` al `write` de `action_cancelar_pago` en `recibo.py`. | pendiente |

---

Lote resuelto el **2026-05-27** (commits `407af41` + `7ba6570`, rama `desarrollo`; verificado en `sandbox_bca1`: 87 tests, 0 failures, 0 errors).

| ID | Vista / Origen | Descripción | Tipo | Prioridad | Solución | Commit |
|----|----------------|-------------|------|-----------|----------|--------|
| BUG-001 | Póliza (form) | No existía el filtrado en cascada Aseguradora → Ramo → Productos. | UI/Lógica | 🟠 Alta | `ramo` computed-editable + domain dinámico en `producto_id` por aseguradora y ramo. | 407af41 |
| BUG-002 | Póliza (form) | Validar que fecha_fin no sea menor que fecha_inicio. | Lógica | 🟡 Media | Ya existía la constraint `_check_fechas` (fecha_inicio < fecha_fin); validado y reforzado por BUG-003. | 407af41 |
| BUG-003 | Póliza (form) | No se calculaba automáticamente fecha_fin desde periodicidad/temporalidad. | Lógica | 🟡 Media | Onchange editable: Vida = inicio + temporalidad_anios; otros = inicio + 1 año. | 407af41 |
| BUG-004 | Póliza (form, Importes) | Campos monetarios sin alineación derecha / formato moneda. | UI/UX | ⚪ Baja | `widget="monetary"` en importes de póliza y recibo. | 407af41 |
| BUG-005 | Póliza | Generación de recibos: Anual + 10 años generaba 1 recibo; Mensual + 10 años habría generado 120. | Lógica | 🟠 Alta | Generación **por anualidad** con avance automático al pagar el último pendiente (+ botón manual). Máx ~12 recibos abiertos. | 407af41 |
| BUG-006 | Recibo (form/lista) | "Nuevo" asignaba folio con lógica opaca; debía llevar al recibo pendiente más antiguo. | UI/UX | 🟡 Media | Onchange `poliza_id` previsualiza el pendiente FIFO; `create()` redirige al recibo pendiente existente. | 407af41 |
| BUG-007 | Recibo (form, Importes) | Todos los importes eran editables; solo "el pago" debía serlo. | Lógica/UI | 🟡 Media | `monto_modal`/`recargo`/`prima_neta` readonly (vienen del plan); solo `prima_total` editable. | 407af41 |
| BUG-008 | Recibo (form, Datos del Pago) | "Conducto" podía quedar en blanco al cobrar. | Lógica/UI | 🟡 Media | `required` en vista (pendiente) + guard en `action_registrar_pago_ui`. | 407af41 |
| BUG-009 | Recibo (lista) | Al agrupar por agente, los recibos pendientes caían en el grupo "Ninguno". | UI/Lógica | 🟡 Media | Campo `agente_poliza_id` (related stored del agente vigente); el filtro de grupo lo usa. | 407af41 |
| BUG-010 | Contactos (form) | Los smart buttons de Pólizas y Recibos no eran visibles en contratantes ni agentes (no existían). | UI/UX | 🟠 Alta | Contadores `bca_poliza_count`/`bca_recibo_count` + acciones + stat buttons en el button_box. | 407af41 |
| BUG-011 | Recibo (form) | "Cancelar Pago" anulaba el recibo (estado cancelado) en vez de deshacer el pago. | Lógica | 🟠 Alta | `action_cancelar_pago` revierte a 'pendiente' con guardia FIFO; nuevo `action_anular_recibo` → 'cancelado'. | 407af41 / 7ba6570 |
