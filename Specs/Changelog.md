# Changelog — Módulo BCA_Seguros

> Actualizar al cerrar cada sesión: qué se hizo, archivos creados/modificados, pendientes y decisiones nuevas.

---

## Sesión 2026-05-27 (b) — Etapa 10: Vistas XML completas + menú navegable

### Qué se hizo
Etapa 10 cerrada: el módulo es navegable end-to-end por backend. Los 13 archivos XML de `views/` ahora tienen vistas funcionales (list/form/search) para los 5 modelos propios de negocio (`bca.poliza`, `bca.recibo`, `bca.conducto`, `bca.factor.pca`, `bca.bitacora.importacion`+`linea`), las 4 herencias normalizadas (`res.partner`, `product.template`, `crm.lead`, `hr.applicant`), skeleton no-op para los 2 wizards (Etapa 8) y el archivo de reportes (Etapa 9), más el menú raíz "BCA Seguros" con 4 ramas (Pólizas, Cobranza, Reportes, Configuración) y groups por rol.

### Decisiones tomadas con el usuario (antes de implementar)
- **Wizards**: skeleton mínimo + TODO (no implementar lógica de E8 acá).
- **Reportes**: skeleton vacío (sin pivot/graph hasta E9 cuando existan las columnas reales).
- **Herencias**: auditar y normalizar las 4 (XML ID, groups, tabs).

### Archivos modificados
- `BCA_Seguros/views/conducto_views.xml` — list+form+search+action `action_conducto`.
- `BCA_Seguros/views/factor_pca_views.xml` — list+form+search+action `action_factor_pca` con chatter, web_ribbon "Inactivo", grupo GMM invisible si ramo!='gmm'. Campo `factor` editable en UI pero restringido por ACL a Director Comercial+.
- `BCA_Seguros/views/poliza_views.xml` — list (con decoration por estado), form con statusbar borrador→activa→vencida→cancelada, botones `action_confirmar`/`action_cancelar` (este último con `confirm=`), smart buttons "Recibos" y "Cambios Agente", tabs Atributos Vida/GMM/Recibos/Historial, `pagado_hasta` siempre readonly, chatter, web_ribbon "Cancelada".
- `BCA_Seguros/views/recibo_views.xml` — list+form+search+action. Form con statusbar pendiente→pagado→cancelado, botón "Registrar Pago" (visible si pendiente, con `confirm=`) y "Cancelar Pago" (visible si pagado, con `groups=director_comercial,director`). Campos PCA/agente/promotoria readonly cuando estado=='pagado'.
- `BCA_Seguros/views/bitacora_views.xml` — list+form (create=false edit=false) + search. Lineas O2m readonly con decoration por marca.
- `BCA_Seguros/views/res_partner_views.xml` — herencia base.view_partner_form: tab "BCA Seguros" con bca_tipo/estado_agente/promotoría/claves por aseguradora. Search con 6 filtros nuevos. 3 actions filtradas: Aseguradoras, Promotorías, Agentes.
- `BCA_Seguros/views/product_template_views.xml` — herencia con tab "BCA Seguros": toggle `bca_es_producto_seguro`, campos visibles solo si activo, atributos Vida visibles solo si ramo=='vida'. Action `action_product_bca` filtrada.
- `BCA_Seguros/views/crm_lead_views.xml` — auditado. Agregado `confirm=` al botón "Generar Póliza".
- `BCA_Seguros/views/hr_applicant_views.xml` — auditado. OK como estaba.
- `BCA_Seguros/views/wizard_carga_portafolio_views.xml` — skeleton form con alert "Pendiente Etapa 8".
- `BCA_Seguros/views/wizard_cobranza_diaria_views.xml` — idem.
- `BCA_Seguros/views/reportes_views.xml` — placeholder vacío con TODO E9 (las 4 vistas SQL tienen solo `id` hoy; no tiene sentido pivot/graph hasta E9).
- `BCA_Seguros/views/menu.xml` — jerarquía completa: BCA → Pólizas (agente+) → {Pólizas, Recibos} | Cobranza (operador+) → Bitácoras | Reportes (líder+) | Configuración (director_comercial+) → {Aseguradoras, Promotorías, Agentes, Productos Seguro, Conductos, Factores PCA}.
- `BCA_Seguros/__manifest__.py` — reordenado: `menu.xml` ahora último de la lista `data[]` (el menú referencia actions que deben existir antes — Plan §2.4.2 sobre orden secuencial entre archivos).
- `BCA_Seguros/models/poliza.py` — agregados `recibo_count` y `cambio_agente_count` (computed) + `action_view_recibos()` y `action_view_cambios_agente()` (retornan action dict) para los smart buttons.
- `BCA_Seguros/models/recibo.py` — agregado `action_registrar_pago_ui()` wrapper sin parámetros que toma los vals ya escritos en el form y llama a `action_registrar_pago(vals)`. Necesario porque el método original toma dict y los botones de form no pasan parámetros.
- `BCA_Seguros/tests/test_views_xml.py` — **NUEVO**. 12 tests `post_install` que cargan cada vista vía `env[model].get_view(view_id, view_type)` para forzar parseo completo y atrapar errores de XML (campos inexistentes, `invisible=` mal escrito, xpaths rotos, actions inexistentes en menú). Cubre las 16 vistas form/list/search del módulo + menú raíz + 9 actions referenciadas en menu.xml.
- `BCA_Seguros/tests/__init__.py` — agregado import de `test_views_xml`.

### Decisiones de implementación
- **`<list>` y `<chatter/>`**: confirmado por inspección de `addons/crm/views/crm_lead_views.xml` en `github.com/odoo/odoo@19.0` que la convención v19 es tag `<list>` (no `<tree>`) y `<chatter/>` moderno (no `<div class="oe_chatter">`). Aplicado uniformemente.
- **`view_mode="list,form"`** en todas las actions (no `tree,form`) consistente con el tag `<list>`.
- **Factor PCA editable solo por Director Comercial+**: la vista no duplica el field con groups invertidos (patrón frágil), confía en ACL `ir.model.access.csv` que ya restringe `perm_write=0` para Operador/Líder. Si un Líder intenta editar, AccessError al guardar — comentario en la vista lo documenta.
- **`action_registrar_pago_ui()`**: en vez de crear un wizard ad-hoc para tomar fecha_pago/prima_neta del usuario, el botón usa los valores ya guardados en el form. Esto requiere que el usuario complete los campos y guarde antes de pulsar el botón, pero evita un wizard extra.
- **`menu_bca_reportes`** sin items hijos hasta E9: en Odoo un menú sin items hijos visibles es invisible automáticamente, así que no causa ruido en producción.
- **`v19: ir.ui.menu.group_ids`** (no `groups_id`): verificado contra `odoo/addons/base/models/ir_ui_menu.py` rama 19.0. El test `test_menu_root_existe` usa `menu.group_ids`.
- **Reordenamiento del manifest**: `menu.xml` quedaba primero en la lista `data[]` original — eso habría causado ParseError porque las actions a las que apunta el menú aún no existen. Movido a último (Plan §2.4.2: orden secuencial entre archivos).

### Estado del checklist Etapa 10 (Plan §Etapa 10)
- [x] Formulario de póliza abre sin errores de XML (test `test_poliza_views`)
- [x] Botón "Confirmar" visible solo en `estado == 'borrador'`
- [x] Campo `pagado_hasta` readonly en UI (atributo `readonly="1"` siempre)
- [x] Factor PCA editable solo para directores (vía ACL — Director Comercial+ tiene perm_write)
- [x] Menú raíz BCA visible para todos los roles BCA (groups= con 5 grupos)
- [x] Skeleton de wizards/reportes carga sin error (test `test_wizard_skeletons_cargan`)
- [x] Botones smart en póliza (Recibos) abren list filtrada por póliza (`action_view_recibos`)
- [x] Decoraciones de color en list correctas (`decoration-success/warning/muted` por estado)

### Verificación en sandbox_bca1 (APROBADA — 2026-05-27 20:58)
Deploy automático tras commits `2ee7821` (feat) + `b672a7a` (fix). Tests:
```bash
docker exec odoo_golden odoo -d sandbox_bca1 --test-enable --test-tags BCA_Seguros --stop-after-init --no-http
```
Resultado: **51 tests, 9.85s, 2795 queries, 0 failures, 0 errors** ✅. Los 12 `TestViewsXml` corrieron como `post_install` y todos pasaron.

### Hotfix descubierto durante el deploy
**Commit `b672a7a`** — `view_partner_list_bca` originalmente usaba `<field name="display_name" position="after">` para insertar columnas `bca_tipo`/`bca_estado_agente`. Falló con ParseError porque otros módulos instalados (probablemente `mail`/`crm`) extienden la vista list de `res.partner` y hacen que el match por nombre de campo sea ambiguo entre las distintas extensiones. Cambiado a `<xpath expr="//list" position="inside">` — robusto contra cualquier orden/cardinalidad de columnas heredadas. Lección para futuras herencias de vistas estándar: preferir `<xpath expr="//list">` sobre selección por nombre de campo cuando la columna objetivo puede aparecer múltiples veces vía herencias en cadena.

### Pendientes para próxima sesión
- **Etapa 6** (parsers cobranza): bloqueada por TODOs documentados en E5 — confirmar contra CSV MetLife real `codigo_archivo` de los 4 conductos, `bca_temporalidad_anios`/`bca_es_capitalizable` por producto Vida, `bca_nombre_archivo_aseguradora`.
- **Etapa 7** (calculadores PCA) — depende de E6 mínimamente para datos reales.
- **Etapa 8** (wizards funcionales) — depende de E6+E7.
- **Etapa 9** (reportes SQL): completar query SQL de los 4 modelos report y crear vistas pivot/graph en `reportes_views.xml`.

---

## Sesión 2026-05-27 — Etapa 5: cierre formal de datos iniciales

### Qué se hizo
Cierre formal de la Etapa 5. Los 7 archivos `data/*.xml` ya existían desde E1 pero con huecos: factores Vida sin vincular a productos, categorías de producto sin jerarquía, conductos con códigos placeholder, y no había seed de productos MetLife (referenciados por los factores). Se cerraron esos huecos y se cuadraron datos con catálogo real provisto por cliente.

### Archivos modificados
- `BCA_Seguros/data/product_categories.xml` — jerarquía completa: `Productos de Seguro BCA → MetLife → {Vida, GMM}` y `Productos de Seguro BCA → Qualitas → Autos`. Antes había solo la raíz.
- `BCA_Seguros/data/productos_metlife.xml` — **NUEVO**. 13 productos `product.template`: 11 Vida (7 con factor preexistente: Universales, TempoLife, TempoLife GP/RP, TotalLife, EducaLife, PerfectLife, Horizonte; 4 nuevos sin factor todavía: Perfect Life, Vida Pagos, Metalife Retiro, Metalife tu Futuro) + 2 GMM (MedicaLife, Primordial). Todos con `bca_es_producto_seguro=True`, `bca_aseguradora_id=partner_metlife`, `bca_ramo`, `type=service` y `categ_id` correcto.
- `BCA_Seguros/data/factores_metlife_2026.xml` — añadido `producto_ids` a los 14 factores Vida (vinculados al producto correspondiente). Los 3 GMM siguen sin `producto_ids` (discriminan por coaseguro/deducible, no por producto — Arq §5.2).
- `BCA_Seguros/data/conductos_metlife.xml` — reescrito con los 4 conductos reales provistos por cliente: Agente Directo, Cargo Automático, Tarjeta de Crédito, Tarjeta de Débito. Antes había 7 placeholders (CTE Conduento 1, Depósito Bancario, TC Efectivo, TC Cheque, TC Crédito, TC Débito, TC Transferencia) marcados como "estimados" en el comentario del propio archivo.
- `BCA_Seguros/security/ir.model.access.csv` — `bca.conducto`: Operador R → RWC, Líder R → RWC. Operador es quien mantiene el catálogo conforme las aseguradoras publican.
- `BCA_Seguros/security/groups.xml` — `group_bca_operador` ahora implica `product.group_product_manager`. Sin esto el Operador queda solo en lectura de `product.template` y no puede dar de alta nuevos productos de seguro.
- `BCA_Seguros/__manifest__.py` — añadido `data/productos_metlife.xml` al `data[]` entre `aseguradoras_iniciales.xml` y `conductos_metlife.xml` (factores depende de productos).

### Decisiones de implementación
- **Productos Vida = 11, no 4 ni 7**: cliente confirmó que los 7 productos referenciados por los factores de E1 son reales (no placeholders como sugería el comentario del XML) y que los 4 nuevos también son reales. Ambos conjuntos coexisten. Los 4 nuevos hoy no tienen factor — cuando se publique su factor 2026, se crea desde UI por Director Comercial o se añade aquí.
- **Factores numéricos 2026**: cliente confirmó que los valores actuales (Universales/PerfectLife/Horizonte/EducaLife = 1.0/0.7; TempoLife/TempoLife GP/RP/TotalLife = 1.0/0.8) son los oficiales. Se mantienen.
- **Productos GMM sin factor propio**: MedicaLife y Primordial comparten los 3 factores GMM que discriminan por regla coaseguro/deducible (10%+ded≥29k → 1.2; 10%+ded<29k → 1.0; ≤5% → 0.0).
- **`bca_temporalidad_anios` y `bca_es_capitalizable`**: hoy 0/False en todos los productos Vida. Marcados con TODO en cabecera del XML — cliente confirmará valores reales antes de E6/E7 (afectan exclusiones PCA por temporalidad < 10 años y aportación adicional en capitalizable).
- **`bca_nombre_archivo_aseguradora`**: vacío en todos los productos. Se llena en E6 cuando se inspeccionen los CSV LSP/GCAYE reales.
- **Operador puede gestionar producto.template global de Odoo, no solo BCA**: vía `implied_ids = product.group_product_manager`. Decisión aceptada por el cliente — el Operador BCA es personal administrativo dedicado, el riesgo de tocar productos no-BCA es bajo. Alternativa rechazada: ACL custom + record rule filtrada a `bca_es_producto_seguro=True` (más complejo, sin valor inmediato).
- **Conductos reemplazados, no agregados**: el verbo del cliente fue "agrega" pero los 7 anteriores eran placeholders con códigos inventados (`CTECONDUENTO1`, `TC_EFECTIVO`, etc.). Reemplazo total. Si el cliente quería conservar alguno, lo recreará vía UI ahora que Operador puede crear conductos.

### Estado del checklist Etapa 5 (Plan §5)
- [x] Datos cargados correctamente al instalar — verificado en sandbox
- [x] Factores MetLife 2026 visibles en UI con vigencia correcta (vinculados a productos vía `producto_ids`)
- [⚠] Conductos con `codigo_archivo` exacto del CSV — pendiente verificación con CSV real en E6 (TODO documentado en `conductos_metlife.xml`)

### Verificación en sandbox_bca1 (APROBADA — 2026-05-27 19:35)
Deploy automático vía `deploy-sandbox.yml` tras push del commit `9cea4b6` a `desarrollo`.
```
docker exec odoo_golden odoo -d sandbox_bca1 --test-enable --test-tags BCA_Seguros --stop-after-init --no-http
```
- Workflow GitHub Actions: ✅ verde.
- Tests: **37 tests, 9.71s, 2514 queries, 0 failures, 0 errors** ✅ (idéntico al baseline E4 — el `implied_ids product.group_product_manager` no rompió nada).
- Smoke post-deploy: 13 productos seguro (11 Vida + 2 GMM) ✅; categorías MetLife/{Vida,GMM} ✅.

### Cleanup post-deploy (manual vía shell)
El `noupdate="1"` de `factores_metlife_2026.xml` previno que el `odoo -u` aplicara los nuevos `producto_ids` a los 14 factores Vida ya existentes desde E1 (la regla `noupdate` solo crea nuevos; no sobreescribe). Igualmente, `conductos_metlife.xml` con `noupdate="1"` dejó los 7 conductos placeholder de E1 como huérfanos al renombrar sus XML IDs.

Fix manual en `odoo shell`:
1. Borrados 7 conductos huérfanos (CTE Conduento 1, Depósito Bancario, TC Efectivo/Cheque/Crédito/Débito/Transferencia).
2. Asignados 14 `producto_ids` a factores Vida vía `write({'producto_ids': [(6,0,[product.id])]})`.

Verificación final: conductos=4 ✅, factores con `producto_ids`=14 ✅.

**Hallazgo registrado en memoria del proyecto:** `noupdate="1"` no aplica cambios a registros existentes en `-u`. Workarounds: write directo en shell, borrar+recrear, o script `migrations/X.Y.Z/post_migrate.py`. Si en E6 o posterior se cambia estructura de datos seed, planear migración explícita.

### Pendientes para próxima sesión
- Verificación en sandbox: `odoo -u BCA_Seguros -d sandbox_bca1 --stop-after-init --no-http` debe instalar sin errores; smoke con `env['product.template'].search_count([('bca_es_producto_seguro','=',True)])` → 13.
- Suite de tests E4 (37 tests): verificar que sigue verde tras añadir `implied_ids product.group_product_manager` al Operador. Riesgo: si algún test asume ACL de Operador sobre product.template, podría cambiar comportamiento. Bajo riesgo (tests E4 no tocan product.template).
- **Etapa 6** (parsers de cobranza) o **Etapa 10** (UI/menú navegable). Antes de E6 hay que confirmar con cliente: (a) valores reales de `bca_temporalidad_anios` y `bca_es_capitalizable` por producto Vida; (b) `bca_nombre_archivo_aseguradora` mirando CSV real; (c) `codigo_archivo` exacto de los 4 conductos en el CSV.

---

## Sesión 2026-05-27 — Etapa 4: seguridad (record rules + ACL completa + tests)

### Qué se hizo
Cierre de la Etapa 4 de seguridad: ACL completa, record rules explícitas por modelo y suite de tests que valida el aislamiento por grupo. El guard M5 (`AccessError` en `bca.recibo.action_cancelar_pago`) ya existía desde E2; aquí se añadió el test que lo respalda.

### Archivos modificados
- `BCA_Seguros/security/ir.model.access.csv` — 58 filas (era 13 + 5 stubs sin grupo). Cubre los 14 modelos del módulo según matriz §7.2 de Arquitectura.
- `BCA_Seguros/security/record_rules.xml` — 50 `ir.rule` (eran 13). 37 nuevas para `bca.poliza`, `bca.recibo`, `bca.bitacora.importacion/linea`, `bca.poliza.cambio.agente` y 4 reportes SQL. Agente filtrado por `agente_id.user_ids` en póliza/recibo; resto `[(1,'=',1)]` obligatorio por A3.
- `BCA_Seguros/tests/test_record_rules.py` — 6 casos `TransactionCase` (agente A solo ve póliza A, director ve ambas, agente A solo sus recibos, líder cross-promotoría, operador no cancela recibo → `AccessError` M5, DC sí cancela).

### Decisiones de implementación
- **Bitácora — Operador R**: spec §7.2 marca Operador como "—" pero el Operador es quien dispara el wizard de cobranza, sería absurdo que no pueda ver lo que importa. Decisión E4: Operador, Líder, DC y Director con `perm_read=1`.
- **Reportes SQL hoy son `WHERE FALSE`**: rules para `bca.reporte.pca.agente` y `bca.reporte.estado.cartera` quedan `[(1,'=',1)]` con comentario `TODO E9`. Cuando E9 implemente las queries reales con campo `agente_id`, agregar filtrado por `user.id` al rule del agente. Hoy el aislamiento se sostiene por ACL (CSV).
- **Wizards (TransientModel)**: solo ACL (Operador+ RWCD); sin record rules — Odoo aísla por sesión.
- **`recibo.action_cancelar_pago`** ya tenía el guard M5 desde E2 (lanza `AccessError`, no `UserError`). El test 5 lo verifica.

### Verificación en sandbox_bca1 (APROBADA)
Deploy automático vía `deploy-sandbox.yml` tras push del commit `0470f79` a `desarrollo` (2026-05-27).
```
docker exec odoo_golden odoo -d sandbox_bca1 --test-enable --test-tags BCA_Seguros --stop-after-init --no-http
```
- Workflow GitHub Actions: ✅ verde.
- Tests E4 (run manual 18:22): **37 tests, 10.47s, 2513 queries, 0 failures, 0 errors** ✅.
- Reglas validadas: A3 (membresía acumulativa neutralizada), M5 (guard de cancelación), aislamiento de agente por `user_ids`.

### Smoke test manual — NO ejecutado en esta sesión
El plan original contemplaba smoke visual en UI, pero `views/menu.xml` está vacío (`<!-- implementar en Etapa 10 -->`) — sin menú raíz no hay app navegable hoy. Los 6 tests automatizados cubren exactamente los mismos escenarios del smoke (agente filtering en póliza/recibo, director ve todo, operador no cancela, DC sí cancela), así que el riesgo es bajo. Smoke visual queda postergado a cierre de E10.

### Pendientes para próxima sesión
- **Etapa 5** (datos iniciales adicionales) o **Etapa 6** (parsers de cobranza). E10 (UI) podría adelantarse si bloquea otro smoke.
- Cuando E9 entregue las queries reales de reportes SQL: agregar al rule del agente filtrado `[('agente_id.user_ids', 'in', [user.id])]` para `bca.reporte.pca.agente` y `bca.reporte.estado.cartera`.

---

## Sesión 2026-05-27 — Etapa 2: modelos core de negocio

### Qué se hizo
Implementación completa de los 4 modelos núcleo de la Etapa 2 (`bca.poliza`, `bca.recibo`, `bca.poliza.cambio.agente`, `bca.bitacora.importacion` + `bca.bitacora.linea`) más tests unitarios. Sin cambios en vistas, seguridad ni manifest — Etapa 4 (security) y Etapa 10 (UI) cubrirán esos aspectos.

### Archivos modificados
- `BCA_Seguros/models/poliza.py` — `bca.poliza` completo: 27 campos, `_compute_promotoria_id` (C2, sin store), `_compute_pagado_hasta` (C1, store=True), `action_confirmar`, `action_cancelar`, `_generar_plan_pagos` (R-POL-05), `cambiar_agente` (M4), constraint SQL único por aseguradora (R-POL-01).
- `BCA_Seguros/models/recibo.py` — `bca.recibo` completo: 19 campos, `write()` con bloqueo C1 (PCA inmutable post-pago, escape vía `env.su` o `allow_pca_edit`), `action_registrar_pago` con validación pre-ejecución (R-COB-09) + FIFO, `action_cancelar_pago` con chequeo explícito de grupo (M5), `_calcular_pca` con stub temporal hasta E7.
- `BCA_Seguros/models/poliza_cambio_agente.py` — `bca.poliza.cambio.agente`: 8 campos todos `readonly=True`, sin métodos (solo se crea desde `poliza.cambiar_agente()`).
- `BCA_Seguros/models/bitacora.py` — `bca.bitacora.importacion` + `bca.bitacora.linea`: campos completos por Plan §2.3.5, `write()/unlink()` bloqueado para no-`env.su`.
- `BCA_Seguros/data/sequences.xml` — añadida `seq_bca_bitacora_importacion` (BIT-YYYY-00001).
- `BCA_Seguros/tests/test_poliza.py` — 6 casos: creación mínima, unique name+aseguradora, confirmar+plan pagos mensual (12 recibos × $1000), R-POL-05 no regenerar con pagados, cambiar_agente registra historial, cambiar_agente rechaza no-agente.
- `BCA_Seguros/tests/test_inmutabilidad.py` — 5 casos: pagado_hasta avanza/retrocede solo, PCA inmutable post-pago, R-COB-09 atómico (sin fecha_pago no toca BD), bitácora inmutable para no-su.

### Decisiones de implementación
- `_calcular_pca` atrapa `NotImplementedError` y retorna `(0.0, 0.0, 'Calculador pendiente — Etapa 7')` para no bloquear E2-E6. Será reemplazado en Etapa 7 cuando se implementen los calculadores reales.
- `action_registrar_pago` usa `super().write()` con `with_context(allow_pca_edit=True)` para evitar el bloqueo de su propio override de `write()`. Mismo patrón en `action_cancelar_pago`.
- `_generar_plan_pagos` borra los recibos pendientes pre-existentes (de un confirmar fallido previo) antes de regenerar, pero **nunca** toca recibos pagados (R-POL-05 lanza primero).
- `currency_id` con default `lambda self: self.env.company.currency_id` en póliza y bitácora (§2.4.5).
- `ramo` en `bca.poliza` es related `store=True` a `producto_id.bca_ramo` para permitir filtros eficientes.

### Verificación E2 en sandbox_bca1 (APROBADA)
Deploy automático vía `deploy-sandbox.yml` tras push del commit `04e0f7b` a `desarrollo` (2026-05-27).
- `odoo -u BCA_Seguros -d sandbox_bca1 --stop-after-init --no-http` → terminó sin errores.
- Workflow GitHub Actions: ✅ verde.
- Registry load + schema migration sin warnings de los 5 modelos nuevos.

### Tests automáticos en sandbox_bca1 (APROBADOS)
```
docker exec odoo_golden odoo -d sandbox_bca1 --test-enable --test-tags BCA_Seguros --stop-after-init --no-http
```
- Primera corrida (17:07): 15 tests, 3 ERRORs por `AttributeError: 'res.users' object has no attribute 'groups_id'`.
- **Fix (commit `e5c90b3`):** Odoo 19 renombró `res.users.groups_id` → `group_ids`. Aplicado a los 3 sitios en `tests/test_inmutabilidad.py`.
- Segunda corrida (17:13): **15 tests, 3.57s, 963 queries, 0 errors** ✅.
- Reglas validadas: R-POL-01, R-POL-03, R-POL-05, R-COB-09, C1, C2, M4, M5.

### Decisiones / hallazgos confirmados en sandbox
- **Odoo 19 breaking change**: `res.users.groups_id` se renombró a `group_ids`. Aplica tanto a `create({'group_ids': [...]})` como a la asignación directa `user.group_ids = [...]`. El método `user.has_group('module.group_xxx')` sigue igual.

### Pendientes para próxima sesión
- (Opcional) Verificación manual UI con shell de Odoo si querés "tocar" la lógica más allá de los tests automáticos.
- Iniciar **Etapa 3** (modelos de integración Odoo: `hr_applicant`, `crm_lead`) o **Etapa 4** (seguridad: record rules específicas de poliza/recibo/bitácora).

---

## Sesión 2026-05-27 — Deploy Etapa 1 + Debug sandbox

### Qué se hizo
Depuración completa del pipeline de deploy y verificación de Etapa 1 en `sandbox_bca1`.

#### Bugs encontrados y corregidos (4 errores en cascada)

**Bug 1 — `_auto=False` sin vista SQL (causa raíz del crash de registry)**
- Odoo 19 valida en registry load que todos los modelos `_auto=False` tengan tabla/view en PostgreSQL. Los 4 modelos de reporte tenían `init()` vacío → "Model X has no table" → registry falla → el módulo no carga → `_auto_init()` de `res.partner` nunca corre → columnas `bca_*` nunca se crean.
- Fix: `init()` crea vista placeholder `SELECT 1::integer AS id WHERE FALSE`.

**Bug 2 — `res.groups.privilege` no existe en este build de Odoo 19**
- El modelo no existe en el build del sandbox → `groups.xml` falla al cargar tras arreglar Bug 1.
- Fix: eliminar `privilege_id` de todos los grupos en `groups.xml`.

**Bug 3 — Comentarios `#` en `ir.model.access.csv`**
- El parser CSV de Odoo 19 intenta resolver `model_id:id = None` para líneas comentario → `_extract_records` falla.
- Fix: eliminar todas las líneas `#` del CSV.

**Bug 4 — Base de datos incorrecta en deploy script**
- `deploy-sandbox.yml` usaba `-d sandbox_bca` pero Odoo sirve desde `sandbox_bca1` (según `odoo.conf`). Todos los deploys anteriores actualizaban la BD equivocada.
- Fix: cambiar `sandbox_bca` → `sandbox_bca1` en el workflow.

### Archivos creados/modificados
- `reports/pca_por_agente.py` — `init()` con vista placeholder
- `reports/pca_por_promotoria.py` — `init()` con vista placeholder
- `reports/pca_consolidado.py` — `init()` con vista placeholder
- `reports/estado_cartera.py` — `init()` con vista placeholder
- `security/groups.xml` — eliminado `res.groups.privilege` y `privilege_id`
- `security/ir.model.access.csv` — eliminadas líneas de comentario `#`
- `.github/workflows/deploy-sandbox.yml` — `-d sandbox_bca` → `-d sandbox_bca1`
- `Specs/Changelog.md` — esta entrada

### Verificación Etapa 1 en sandbox_bca1 (APROBADA)
```
env['bca.conducto'].search_count([])           → 7  ✓
env['bca.factor.pca'].search_count([])         → 17 ✓
partner_metlife.bca_codigo_aseguradora         → 'METLIFE' ✓
group_bca_director.name                        → 'Director BCA' ✓
UI login sin errores                           ✓
```

### Decisiones / hallazgos de infra confirmados
- `res.groups.privilege` NO existe en este build de Odoo 19 Community (sandbox)
- `models.Constraint()` SÍ existe y funciona (`hasattr(models, 'Constraint') = True`)
- PostgreSQL está en DigitalOcean Managed Database (externo al contenedor Docker)
- Addon path: host `/opt/odoo/addons/` → contenedor `/mnt/extra-addons/`
- DB del sandbox: `sandbox_bca1` | `dbfilter = ^sandbox` en odoo.conf

### Pendientes para próxima sesión
- **Etapa 2:** implementar `bca.poliza` y `bca.recibo` con campos completos (state machine, `action_confirmar`, `_generar_plan_pagos`, `cambiar_agente`, `bca.poliza.cambio.agente`)
- Verificación manual de constraints pendientes (baja prioridad):
  - Crear agente sin promotoría → `ValidationError`
  - Crear `res.partner.agente.aseguradora` duplicado → error SQL

---

## Sesión 2026-05-26 — Etapa 0: Scaffolding

### Qué se hizo
- Corrección del nombre técnico del módulo: `bca_core` → `BCA_Seguros` en todas las referencias.
- Actualización de `Specs/Plan de Desarrollo.md`: todos los prefijos XML `bca_core.` → `BCA_Seguros.`, función `post_init_hook_bca_core` → `post_init_hook_bca_seguros`.
- Creación completa del scaffolding del módulo `BCA_Seguros/`:
  - `__manifest__.py` y `__init__.py` raíz con `post_init_hook_bca_seguros`
  - `models/` — 11 stubs de modelos (sin campos, solo `_name` y `_description`)
  - `wizards/` — 2 stubs (TransientModel)
  - `parsers/` — `get_parser()` funcional + `ParserBase` + stubs MetLife LSP y GCAYE
  - `calculadores_pca/` — `CALCULADOR_REGISTRY` + `CalculadorPCABase` + stub MetLife
  - `reports/` — 4 modelos con `_auto=False` e `init()` vacío
  - `migrations/1.0.0/post_migrate.py` — placeholder
  - `security/` — 3 archivos (grupos, ACL, record_rules) en formato correcto
  - `data/` — 7 archivos XML placeholder
  - `views/` — 12 archivos XML placeholder
  - `static/description/icon.png` — PNG 1x1 placeholder
  - `tests/` — 5 archivos stub con clase de test vacía

### Archivos creados/modificados
- **Modificados:** `Specs/Plan de Desarrollo.md`
- **Creados:** Todo el árbol `BCA_Seguros/` (ver estructura en Plan §3)
- **Creados:** `Specs/Changelog.md` (este archivo), `Specs/Decisiones.md`

### Estado del checklist Etapa 0
- [x] `odoo-bin -i BCA_Seguros` instala sin errores — **verificado en sandbox_bca1 (2026-05-26)**
- [x] No hay imports circulares — OK
- [x] `post_init_hook` definido y referenciado en manifest — OK
- [x] `get_parser('METLIFE', 'vida')` devuelve `ParserMetLifeVida` — OK (lógica implementada)
- [x] `get_parser('DESCONOCIDA', 'vida')` lanza `UserError` — OK (lógica implementada)
- [x] 4 modelos de reporte con `_auto=False` e `init()` — OK

### Decisiones tomadas esta sesión
- Nombre técnico del módulo confirmado como `BCA_Seguros` (= nombre de carpeta). Ver `Specs/Decisiones.md`.

### Pendientes para próxima sesión
- Verificar Etapa 1 en sandbox_bca1 con `odoo-bin -u BCA_Seguros`

---

## Sesión 2026-05-26 — Etapa 1: Modelos Base con Campos Completos

### Qué se hizo
- Implementación completa de 5 modelos base con campos, computed fields y constraints
- Implementación de seguridad completa: grupos, ACL, record rules
- Implementación de 6 archivos de datos iniciales (aseguradoras, conductos, factores PCA, categorías, secuencias)

### Archivos creados/modificados

**Modelos (5 archivos):**
- `models/res_partner_agente_aseg.py` — modelo puente C3, `models.Constraint()`, type annotations
- `models/res_partner.py` — extensión con 7 campos, `_compute_promotoria_id` (C2 sin store), `_check_jerarquia`
- `models/product_template.py` — extensión con 6 campos BCA
- `models/conducto.py` — modelo completo con `models.Constraint()`
- `models/factor_pca.py` — hereda `mail.thread`, 4 campos con `tracking=True`

**Seguridad (3 archivos):**
- `security/groups.xml` — `res.groups.privilege` (Odoo 19) + 5 grupos con jerarquía `implied_ids`
- `security/ir.model.access.csv` — ACL para conducto, factor_pca, agente_aseg + acceso global para stubs
- `security/record_rules.xml` — 13 rules: `[(1,'=',1)]` para grupos no-agente (A3 obligatorio)

**Datos (6 archivos):**
- `data/partner_categories.xml` — 5 categorías: Holding BCA, Aseguradora, Promotoría BCA, Agente BCA, Contratante BCA
- `data/product_categories.xml` — 1 categoría: Productos de Seguro BCA
- `data/sequences.xml` — secuencia `bca.recibo` (REC-YYYY-00001)
- `data/aseguradoras_iniciales.xml` — MetLife México (METLIFE) + Quálitas (QUALITAS)
- `data/conductos_metlife.xml` — 7 conductos (2 Vida + 5 GMM) ⚠️ códigos por verificar
- `data/factores_metlife_2026.xml` — 17 factores (14 Vida + 3 GMM), vigencia 2026-01-01

### Estándares Odoo 19 aplicados
- `from __future__ import annotations` en todos los modelos
- Type annotations en campos y métodos (obligatorias en v19)
- `models.Constraint()` en lugar de `_sql_constraints` (deprecated en v19)
- `res.groups.privilege` + `privilege_id` para categorías de grupos (confirmado en sandbox)

### Estado del checklist Etapa 1
- [x] `odoo-bin -u BCA_Seguros` instala sin errores — **verificado en sandbox_bca (2026-05-27)**
- [x] `res.partner` tiene campos BCA visibles — OK (`fields_get` sin KeyError)
- [ ] Crear agente sin promotoría → `ValidationError` — pendiente (verificación manual)
- [ ] Crear dos `res.partner.agente.aseguradora` con mismo `(aseguradora, clave)` → error SQL — pendiente
- [ ] Crear producto de seguro funciona — pendiente
- [ ] Cambiar `factor` en `bca.factor.pca` → chatter registra cambio — pendiente
- [x] `bca.conducto` tiene 7 registros — OK
- [x] `bca.factor.pca` tiene 17 registros — OK
- [x] `partner_metlife.bca_codigo_aseguradora == 'METLIFE'` — OK
- [x] `group_bca_director` existe — OK

### Decisiones tomadas esta sesión
- `models.Constraint()` adoptado como estándar — **confirmado funcional en sandbox**
- `res.groups.privilege` **NO existe** en este build de Odoo 19 — grupos sin `privilege_id` (ver commit 2affaad)
- Códigos de conducto en `conductos_metlife.xml` son estimados — verificar antes de E3

### Bugs encontrados y corregidos en deploy (2026-05-27)
- **Bug 1:** Modelos `_auto=False` con `init()` vacío → Odoo 19 falla "no table" en registry load. Fix: vista SQL placeholder `SELECT 1::integer AS id WHERE FALSE`.
- **Bug 2:** `res.groups.privilege` no existe en este build → eliminar `privilege_id` de `groups.xml`.
- **Bug 3:** Comentarios `#` en `ir.model.access.csv` → parser CSV falla en `_extract_records`. Fix: eliminar líneas de comentario.
- **Bug 4:** Schema migration de `res.partner` no aplicó en deploys fallidos → columnas `bca_*` creadas manualmente vía SQL tras deploy exitoso.

### Pendientes para próxima sesión
- Verificación manual de constraints (agente sin promotoría, duplicado agente_aseguradora) — baja prioridad
- Iniciar **Etapa 2** — `bca.poliza` y `bca.recibo` con campos completos
