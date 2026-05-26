# Changelog — Módulo BCA_Seguros

> Actualizar al cerrar cada sesión: qué se hizo, archivos creados/modificados, pendientes y decisiones nuevas.

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
- [ ] `odoo-bin -i BCA_Seguros` instala sin errores — **pendiente verificar en servidor**
- [ ] No hay imports circulares — revisión visual OK
- [ ] `post_init_hook` definido y referenciado en manifest — OK
- [ ] `get_parser('METLIFE', 'vida')` devuelve `ParserMetLifeVida` — OK (lógica implementada)
- [ ] `get_parser('DESCONOCIDA', 'vida')` lanza `UserError` — OK (lógica implementada)
- [ ] 4 modelos de reporte con `_auto=False` e `init()` — OK

### Decisiones tomadas esta sesión
- Nombre técnico del módulo confirmado como `BCA_Seguros` (= nombre de carpeta). Ver `Specs/Decisiones.md`.

### Pendientes para próxima sesión
- Verificar instalación en Odoo Sandbox (`sandbox-odoo.habitatdigital.net`, DB `sandbox_bca1`)
- Iniciar **Etapa 1** — Modelos base con campos completos
