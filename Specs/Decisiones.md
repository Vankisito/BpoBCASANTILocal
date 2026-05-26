# Decisiones Técnicas — Módulo BCA_Seguros

> Registrar aquí toda decisión técnica o de diseño no obvia. Incluir: qué se decidió, por qué, quién lo aprobó y cuándo. Esto evita repetir conversaciones ya resueltas.

---

## D-01 — Nombre técnico del módulo: `BCA_Seguros`

**Fecha:** 2026-05-26  
**Decidido por:** Rafael Viera (usuario)

**Decisión:** El nombre técnico del módulo (nombre de carpeta que Odoo usa como identificador interno) es `BCA_Seguros`.

**Consecuencias:**
- Todos los XML external IDs usan prefijo `BCA_Seguros.` (ej: `BCA_Seguros.group_bca_agente`)
- Todos los `ref=` en XML usan `BCA_Seguros.algo`
- Los atributos `groups=` en vistas usan `groups="BCA_Seguros.group_bca_..."`
- La función de hook se llama `post_init_hook_bca_seguros`
- Los nombres de modelo ORM (`_name = 'bca.poliza'`) son **independientes** del nombre del módulo y no cambian

**Nota:** La versión anterior de las specs usaba `bca_core` como prefijo. Fue corregido en `Specs/Plan de Desarrollo.md` en la sesión 2026-05-26.

---

## D-02 — Agentes son usuarios internos de Odoo (no portal)

**Fecha:** Sesión previa (antes de 2026-05-26)  
**Referencia:** `Plan de Desarrollo.md §2.0`

**Decisión:** Los agentes inician sesión en el **backend** de Odoo (`share=False`). No son usuarios portal.

**Consecuencias:**
- No existe `/my/polizas` ni ninguna ruta portal
- El módulo `portal` no es dependencia de `BCA_Seguros`
- El grupo se llama `group_bca_agente` (no `group_bca_agente_portal`)
- Las record rules del backend los restringen a ver solo sus pólizas

---

## D-03 — `promotoria_id` en póliza es computed puro (sin `store=True`)

**Fecha:** Sesión previa  
**Referencia:** Corrección C2 en `Arquitectura_BCA_Seguros.md §13`

**Decisión:** `promotoria_id` en `bca.poliza` es un campo computed sin almacenamiento. Se implementa `_search_promotoria_id()` para mantener filtrabilidad.

**Razón:** Evitar desincronización si el agente cambia de promotoría. El valor siempre se deriva del `parent_id` del agente en tiempo real.
