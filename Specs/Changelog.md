# Changelog — Módulo BCA_Seguros

> Actualizar al cerrar cada sesión: qué se hizo, archivos creados/modificados, pendientes y decisiones nuevas.

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
