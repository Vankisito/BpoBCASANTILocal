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

---

## D-04 — Asegurado: nuevo `bca_tipo='asegurado'` con domain permisivo

**Fecha:** 2026-05-28
**Decidido por:** Rafael Viera (usuario) vía AskUserQuestion

**Decisión:** La persona cuya vida está asegurada se modela como `res.partner`. Se agrega el valor `asegurado` a `bca_tipo` y un campo `bca.poliza.asegurado_id`. El domain de `asegurado_id` es **permisivo**: `['|', ('bca_tipo','=','asegurado'), ('bca_tipo','=','contratante')]`.

**Razón:** `bca_tipo` es de **valor único** por contacto. El contratante suele ser su propio asegurado (caso más común); si el domain exigiera estrictamente `bca_tipo='asegurado'`, no se podría apuntar al contratante. El tipo `asegurado` queda para personas que SOLO son asegurados.

---

## D-05 — Beneficiarios: modelo ligado a `res.partner`, validación 100% al confirmar

**Fecha:** 2026-05-28
**Decidido por:** Rafael Viera (usuario) vía AskUserQuestion

**Decisión:** Modelo `bca.poliza.beneficiario` (One2many en la póliza) con `beneficiario_id` → `res.partner`, `parentesco` (Selection) y `porcentaje` (Float). **NO** se fuerza un `bca_tipo` en el beneficiario. La suma de porcentajes debe ser 100%, validada **al confirmar** la póliza (`_validar_porcentaje_beneficiarios` desde `action_confirmar`), **no** como `@api.constrains`.

**Razón:**
- Ligarlo a `res.partner` permite reutilizar datos del contacto y, a futuro, CRM/dirección. Un beneficiario suele ser cónyuge/hijo que podría ser contratante en otra póliza → por eso NO se fuerza `bca_tipo` (incompatible con el valor único, ver D-04).
- Validar al confirmar (y no en cada `write`) permite capturar la póliza en borrador con datos parciales sin que la constraint estorbe.

**Consecuencia de seguridad:** Como el modelo es hijo de la póliza y el agente lo ve en el One2many del form, lleva su propio bloque de `ir.rule` (agente solo de SUS pólizas vía `poliza_id.agente_id.user_ids`; resto `[(1,'=',1)]` por la regla A3 de `implied_ids`).

---

## D-06 — `estatus_pago` es declarativo, no fuente de verdad operativa

**Fecha:** 2026-05-28
**Decidido por:** Rafael Viera (usuario) vía AskUserQuestion

**Decisión:** Se agrega `bca.poliza.estatus_pago` (Selection capturable) para reflejar el "Estatus de Pago" del layout. NO reemplaza ni alimenta la lógica de vigencia de pago: esa la determina el computed `pagado_hasta` a partir de los recibos.

**Razón:** El layout trae un estatus de pago declarativo de la aseguradora. Mantenerlo como dato informativo evita acoplar la cobranza operativa (FIFO + recibos) a un campo que puede quedar desincronizado. Valores tentativos (al corriente / vencido / suspendido) **pendientes de confirmar** con el catálogo real de MetLife.

---

## D-07 — Nomenclatura de carrera del agente: 3 estados, fuente en el puente, rollup computed en el contacto

**Fecha:** 2026-06-05
**Decidido por:** Rafael Viera (usuario) vía AskUserQuestion

**Decisión:** El estado de carrera del agente tiene **tres niveles** —`prospecto` → `clave_arranque` → `clave_definitiva`— y es **por aseguradora**.

- **Fuente de verdad:** `res.partner.agente.aseguradora.estado` (modelo puente), con `default='prospecto'`. Un agente puede tener estado distinto por aseguradora (Definitiva en MetLife, Arranque en Qualitas).
- **`res.partner.bca_estado_agente`** pasa a ser un **rollup computed `store=True`** del puente: el mejor estado alcanzado en cualquier aseguradora (Definitiva > Arranque > Prospecto; sin claves = Prospecto). **No editable a mano.** Solo para filtros/listas/visual.
- **PCA:** solo `clave_definitiva` computa, y se filtra por el estado del **puente** de esa aseguradora (`aa.estado='clave_definitiva'`), **no** por `res.partner.bca_estado_agente`. Filtrar por el rollup sería un bug (corregido en `Arquitectura §6.1`).
- Se **eliminó** `res.partner.bca_fecha_licencia` (redundante): la fecha vive por aseguradora en `res.partner.agente.aseguradora.fecha_licencia`.
- **Reclutamiento (`hr_recruitment`) es dueño del ciclo.** Vía automated actions sobre `hr.applicant`: crea el partner agente en Prospecto, crea el registro puente con `clave_arranque` al aprobar examen, y actualiza a `clave_definitiva` cuando la aseguradora confirma (la transición Arranque→Definitiva también la automatiza Reclutamiento). El contacto refleja el rollup + un **smart button** a `hr.applicant`; el detalle fino de exámenes/etapas vive en Reclutamiento.

**Razón:**
- El puente debe existir igual (claves múltiples + constraint SQL por aseguradora, ver C3). Guardar además un estado manual en el partner duplicaría la fuente → desync. Hacer el partner un rollup computed elimina el desync (misma filosofía que C2/D-03).
- El estado es genuinamente por aseguradora, así que la PCA debe leerlo del puente; un campo global del partner no puede expresarlo correctamente.
- Reclutamiento ya lleva la prospección/exámenes; automatizar la alimentación del puente evita que Operaciones de Seguros tenga que mover estados a mano.

**Pendiente de implementación:** campos destino en `hr.applicant` (`bca_aseguradora_destino_id`, `bca_clave_arranque`), las automated actions del ciclo completo y el smart button. Hoy `hr_applicant.py` solo crea el partner al cerrar "Contratado". El rollup y el puente ya soportan los tres estados.
