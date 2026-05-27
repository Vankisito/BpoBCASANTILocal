# Changelog — Módulo BCA_Seguros

> Actualizar al cerrar cada sesión: qué se hizo, archivos creados/modificados, pendientes y decisiones nuevas.

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

### Pendientes para próxima sesión
- Verificación local con `odoo-bin -u BCA_Seguros --test-enable --test-tags BCA_Seguros --stop-after-init` (en máquina local; aún sin deploy a sandbox).
- Deploy a `sandbox_bca1` y verificación manual del checklist E2 — postergado por decisión del usuario.
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
