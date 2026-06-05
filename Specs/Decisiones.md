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

## D-06 — `estatus_pago` es declarativo, no fuente de verdad operativa  ⚠️ SUPERADA por D-09

**Fecha:** 2026-05-28
**Decidido por:** Rafael Viera (usuario) vía AskUserQuestion
**Estado:** Superada por **D-09** (Etapa 8): `estatus_pago` deja de ser un campo capturable
y pasa a **computed** derivado de la fecha pagada. El espíritu de D-06 (que la verdad
operativa la da `pagado_hasta`) se mantiene y se refuerza.

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

---

## D-08 — PCA multimoneda: factor por moneda de la póliza, resultado convertido a MXN

**Fecha:** 2026-06-05
**Decidido por:** Rafael Viera (usuario) vía AskUserQuestion (Etapa 7)

**Decisión:** El cálculo de PCA (`calculadores_pca/metlife.py`) expresa la PCA **siempre en MXN**.

- **Selección de factor por moneda de la póliza.** En Vida la tabla de factores distingue MXN vs USD (ej. TempoLife 100% MXN / 80% USD). Se selecciona la fila cuyo `currency_id` coincide con `poliza.currency_id` — la póliza USD recibe su factor USD (conserva el "haircut" del 80%). GMM no discrimina por moneda (los 3 factores son MXN).
- **Conversión a MXN al final.** `pca_ccy = prima_neta × factor` (en moneda de la póliza); si la póliza no es MXN, se convierte vía `res.currency._convert(pca_ccy, MXN, company, fecha_pago)`. Matemáticamente equivalente a "convertir antes del factor" (resuelve la corrección M3 de Arquitectura §5.2, que queda obsoleta en su lectura "siempre factor MXN").
- **Campo nuevo `bca.recibo.pca_currency_id`** (default MXN), al que apunta `currency_field` de `pca_aplicada`. Necesario porque la PCA está en MXN aunque la póliza (y `recibo.currency_id`) puedan ser USD. Se congela al pago junto con `pca_aplicada`/`factor_aplicado` (R-PCA-01).
- **Exclusión "coberturas individuales de accidentes/invalidez": fuera de alcance E7.** No existe campo estructurado (solo el texto libre `coberturas_adicionales`); queda como ajuste manual futuro. E7 implementa solo las exclusiones con campo: aportación adicional y temporalidad < 10 (Vida); coaseguro ≤ 5% (GMM).

**Razón:**
- Conservar el factor por moneda mantiene la semántica económica (las pólizas USD sí valen menos PCA), y aun así el resultado queda homogéneo en MXN para reportes y liquidaciones consolidadas.
- Pinear la PCA a su propia moneda (`pca_currency_id`) evita mostrar montos ambiguos cuando la póliza es USD.
- La exclusión por coberturas individuales no es auto-evaluable desde texto libre; forzarla sería adivinar. Mejor dejarla explícita como pendiente que producir PCA incorrecta.

**Hallazgo asociado (deuda de datos):** `bca.poliza.coaseguro` se guarda como **fracción** (0.10 = 10%) mientras que `bca.factor.pca.coaseguro_min` del seed GMM usa **puntos porcentuales** (10.0). El calculador normaliza (`coaseguro_pct = poliza.coaseguro × 100`) antes de comparar. Registrado en `Bugs.md`.

---

## D-09 — `estatus_pago` computed: una sola fuente de verdad para la salud de pago (supera D-06)

**Fecha:** 2026-06-05
**Decidido por:** Rafael Viera (usuario) vía AskUserQuestion (Etapa 8)

**Contexto:** `bca.poliza` tenía dos ejes que parecían redundantes y colisionaban en la palabra "vencida/vencido": `estado` (ciclo de vida contractual: borrador/activa/vencida/cancelada) y `estatus_pago` (salud de pago: al_corriente/vencido/suspendido, editable a mano por D-06). Además `estatus_pago` podía contradecir a `pagado_hasta`, que el propio modelo declara como la verdad operativa.

**Decisión:** `estatus_pago` deja de ser capturable y pasa a **computed `store=True`** (`_compute_estatus_pago`):

- **Derivación:** la fecha de pago efectiva = `pagado_hasta` (recibos pagados) y, en su defecto, `pagado_hasta_inicial` (declarado en la carga de portafolio). Si `fecha + gracia >= hoy` → `al_corriente`, si no → `vencido`. Estados `borrador`/`cancelada` → vacío.
- **`pago_suspendido`** (Boolean, nuevo): único override manual, ya que `suspendido` no es derivable de una fecha.
- **Período de gracia** configurable: `ir.config_parameter` `bca_seguros.dias_gracia_pago` (default 30), semilla en `data/config_parameters.xml`.
- **Aging por tiempo:** como el cómputo depende de "hoy" y es `store=True`, un `ir.cron` diario (`data/cron_estatus_pago.xml` → `_cron_refrescar_estatus_pago`) recalcula las pólizas activas. Deja lista la clasificación de cartera de la Etapa 9.
- **`pagado_hasta_inicial`** (Date, nuevo): dato declarado del layout. `pagado_hasta` (computed desde recibos) sigue siendo la verdad operativa; este campo solo siembra el arranque mientras no haya recibos pagados, y ancla la generación del plan (solo recibos posteriores al corte).
- **Colisión de etiqueta:** la etiqueta de `estado='vencida'` se renombró a **"Expirada"** (la clave `vencida` no cambia → sin migración).

**Razón:**
- Un solo eje de verdad para el pago elimina el riesgo de desincronización que D-06 aceptaba como "informativo". El estatus nunca contradice a los recibos.
- `estado` (lifecycle) y `estatus_pago` (pago) son ejes ortogonales legítimos; el problema era solo el solapamiento semántico y la doble fuente, no la existencia de ambos.
- El `pagado_hasta_inicial` permite cargar pólizas en vigor sin inventar recibos históricos pagados (decisión del usuario en Etapa 8: generar solo recibos posteriores al corte).

**Impacto:** `bca.poliza.estatus_pago` ahora `readonly` en la vista (badge). El layout "Estatus de Pago" ya no se almacena verbatim: "suspendido" → `pago_suspendido=True`; al_corriente/vencido los deriva el computed desde `pagado_hasta_inicial`. Tests que asignaban `estatus_pago` a mano se ajustaron.
