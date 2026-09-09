# Spec Etapa 13 — Alta de Póliza por PDF (OCR determinista + intake por correo)

**Proyecto:** Grupo BCA — Gestión de Pólizas, Cobranza y PCA
**Plataforma:** Odoo Community 19
**Autor:** Hábitat Digital
**Estado:** Propuesto — pendiente de aprobación
**Versión objetivo:** `19.0.1.12.0`
**Depende de:** Etapas 1–2 (modelo `bca.poliza`, flujo `borrador → action_confirmar`), patrón wizard 2 fases (Etapa 6, `wizards/carga_portafolio.py`), Strategy pattern de parsers (`parsers/base.py`).

> **Documentos de referencia obligatorios (leer antes):**
> 1. `Specs/01-cobranza-polizas/Arquitectura_BCA_Seguros.md`
> 2. `Specs/01-cobranza-polizas/diccionario-campos-vida-bca-seguros-v1.md` y `diccionario-campos-gmm-bca-seguros-v1.md`
> 3. `Specs/Decisiones.md`
> 4. Pattern del skill Odoo: `skills/wizard-patterns.md`, `skills/mail-notification-patterns.md`, `skills/controller-api-patterns.md` (leer antes de codificar).

---

## 1. Objetivo

Permitir dar de alta una `bca.poliza` a partir de la **carátula PDF digital** que emite la aseguradora, extrayendo los datos de forma **determinista (sin IA)** y llenando el formulario de la póliza en estado **`borrador`**. El usuario **revisa y autoriza** la creación pulsando el botón existente **Confirmar** (`action_confirmar`).

Dos canales de entrada, **un solo motor de extracción compartido**:

1. **Carga manual** — wizard donde el usuario sube el PDF (vista previa de lo extraído → crea borrador).
2. **Intake por correo** — un `mail.alias` **`polizas`** apuntando directamente a `bca.poliza`: al llegar un correo con PDF adjunto, se extrae y se crea el borrador automáticamente, dejando una **actividad de revisión** asignada al capturista.

**Alcance inicial:** **MetLife**, ramos **Vida** y **GMM**. Nuevas aseguradoras = nuevo extractor (Strategy), sin tocar modelos ni wizard (regla de oro §2.1.7 del Plan).

### 1.1 Fuera de alcance (explícito)
- Cualquier motor con IA/LLM/cloud-AI (decisión del usuario). Solo parsing determinista + OCR clásico por reglas.
- **Auto-confirmación** de la póliza. El pipeline SIEMPRE deja la póliza en `borrador`; la activación (`action_confirmar`, que genera el plan de pagos) es **acto humano**.
- Ramo AUTOS (Qualitas) — igual que en la carga de portafolio.
- Portal de agente (ver D-02).

---

## 2. Motor de extracción (determinista)

### 2.1 Estrategia por capas (sin IA)
1. **Primario — capa de texto:** `pdfplumber` (o `PyMuPDF`) → `extract_text()`. Los PDF de la aseguradora son **digitales**, así que este es el camino normal. Campos por **ancla + regex** definidos en una plantilla por aseguradora/ramo.
2. **Fallback — OCR clásico:** si `extract_text()` devuelve texto vacío/insuficiente (PDF escaneado o aplanado), rasterizar con `pdf2image` y pasar a `pytesseract` (Tesseract, idioma `spa`), luego aplicar las **mismas** anclas/regex sobre el texto OCR. El fallback es determinista (Tesseract sin ML entrenable custom, solo reconocimiento clásico).

> **Detección de camino:** si `len(texto_extraído.strip()) < UMBRAL` (config `bca_seguros.ocr_umbral_texto`, default 40) ⇒ fallback OCR. Se registra en el reporte qué camino se usó.

### 2.2 Strategy pattern (espejo de `parsers/base.py`)
Nuevo paquete `BCA_Seguros/extractors/`:

```
extractors/
  __init__.py
  base.py              # ExtractorPolizaPDFBase + get_extractor()
  metlife_vida.py      # ExtractorMetLifeVida
  metlife_gmm.py       # ExtractorMetLifeGMM
```

- `base.py` — clase `ExtractorPolizaPDFBase`:
  - Atributos de subclase: `aseguradora_codigo`, `ramo`, `anclas` (dict `{campo_poliza: {'regex': ..., 'grupo': 1, 'requerido': bool}}`).
  - `extraer(pdf_bytes) -> dict` : orquesta capa de texto → fallback OCR → aplica anclas → devuelve `{'vals': {...}, 'faltantes': [...], 'camino': 'texto'|'ocr', 'texto_crudo': str}`.
  - Reusa normalizadores existentes (patrón `normalizar_monto`/`normalizar_fecha` de `ParserBase`, mismos formatos `DD/MM/YYYY`, coma como miles). **No duplicar**: mover normalizadores a un helper compartido o heredar.
  - **Nunca** lanza por campo faltante: acumula en `faltantes` (el humano completa). Solo lanza si el PDF es ilegible por completo.
- `get_extractor(aseguradora_codigo, ramo)` — dispatcher (patrón A4, igual que `parsers.get_parser`): resuelve la subclase; error descriptivo si no hay extractor para esa aseguradora/ramo.

### 2.3 Plantillas MetLife (anclas)
- Dos plantillas: **Vida** y **GMM**. Los campos objetivo salen del diccionario de campos existente y del modelo `bca.poliza`:
  `name` (Nº póliza), `producto`, `plan`, `agente` (clave), `contratante` (+ RFC, dirección, contacto), `asegurado`, `moneda`, `periodicidad`, `fecha_inicio`, `fecha_fin`, `fecha_emision`, `prima_anual`, `prima_fraccionada`, `suma_asegurada`, y por ramo: GMM (`deducible`, `coaseguro`, `nivel_hospitalario`, `iva`, `recargo_fraccionamiento`), Vida (`tipo_cobertura`, `temporalidad_anios`).
- **Requerido mínimo para crear el borrador** (si falta alguno ⇒ no se crea, ver §4.3): `name`, `producto` (resoluble), `agente` (clave resoluble), `contratante` (nombre), `moneda`, `periodicidad`, `fecha_inicio`, `fecha_fin`.
- Coberturas/beneficiarios: si la carátula los trae en tabla, extraer con `pdfplumber.extract_tables()` (posicional); si no, dejar vacíos para captura manual. **No** bloquean el alta.

> ⚠️ **Las anclas exactas se calibran contra una carátula PDF real de MetLife.** Igual que los parsers de cobranza traen `TODO Etapa 8: confirmar contra archivo real`, estas plantillas nacen con `TODO Etapa 13: calibrar anclas contra carátula real Vida/GMM`. **Bloqueante para cerrar la etapa.**

### 2.4 Reuso de resolvers (DRY — refactor previo)
`wizards/carga_portafolio.py` ya tiene: `_resolver_agente`, `_resolver_producto`, `_resolver_moneda`, `_resolver_conducto`, `_find_or_create_partner`, `_map_periodicidad`, `_datos_contratante`, normalizadores. **No reimplementar.**

**Refactor previo (paso 0 de la etapa):** extraer esos resolvers a un **`AbstractModel` `bca.poliza.import.mixin`** (`models/poliza_import_mixin.py`) del que hereden tanto el wizard de portafolio como el nuevo wizard/intake de PDF. Así el mapeo `datos_crudos → vals + partners` es único. El extractor produce datos crudos homogéneos (mismas claves que hoy consume `_construir_vals`), y el mixin los convierte a vals + resuelve/crea partners.

---

## 3. Dependencias externas

Añadir a `__manifest__.py` → `external_dependencies.python` (regla §2.4.7: declararlas o el módulo falla en runtime):

```python
'external_dependencies': {
    'python': ['openpyxl', 'pdfplumber', 'pytesseract', 'pdf2image'],
    'bin': ['tesseract', 'pdftoppm'],  # documentar; 'bin' es informativo
},
```

- `pdfplumber` — camino primario (texto). Import protegido `try/except ImportError` como `openpyxl` en `carga_portafolio.py`.
- `pytesseract` + `pdf2image` + binarios **Tesseract** (idioma `spa`) y **Poppler** (`pdftoppm`) — **solo** para el fallback OCR. Import perezoso: si no están instalados y se necesita el fallback ⇒ `UserError` claro ("PDF sin capa de texto y OCR no disponible; instale tesseract-ocr + poppler-utils"). El camino de texto NO debe requerir estos binarios.

> **Nota de despliegue:** documentar en README la instalación de `tesseract-ocr`, `tesseract-ocr-spa` y `poppler-utils` en el server. Si el negocio confirma que los PDF SIEMPRE traen texto, el fallback OCR queda como salvaguarda opcional.

---

## 4. Componentes por canal

### 4.1 Canal manual — Wizard `bca.wizard.alta.poliza.pdf`
`wizards/alta_poliza_pdf.py` (`TransientModel`), hereda `bca.poliza.import.mixin`. Patrón 2 fases igual que `carga_portafolio`:

Campos: `archivo` (Binary PDF), `nombre_archivo`, `aseguradora_id` (default MetLife), `ramo` (selection Vida/GMM), `state` (`cargar`/`previsualizado`), `reporte_html`, `vals_preview` (Text/JSON solo lectura), `faltantes_html`.

Acciones:
- `action_previsualizar()` — **fase 1, dry-run, sin tocar BD:** abre el extractor (`get_extractor`), extrae, resuelve referencias (agente/producto/partner en modo lookup, sin crear), y muestra en `reporte_html` los campos detectados + `faltantes` + camino (texto/OCR). No crea nada.
- `action_crear_borrador()` — **fase 2:** dentro de `with self.env.cr.savepoint()`, crea/resuelve partners y `bca.poliza` en `estado='borrador'`; adjunta el PDF al chatter de la póliza (`ir.attachment` sobre `bca.poliza`); retorna un `act_window` que **abre el form de la póliza** para que el usuario revise y pulse Confirmar.

Vista: `views/wizard_alta_poliza_pdf_views.xml` (form del wizard `target='new'`), acción y entrada de menú bajo Pólizas. Botón adicional en la vista lista/form de `bca.poliza` ("Alta desde PDF") que abre el wizard.

### 4.2 Canal correo — `mail.alias` `polizas` sobre `bca.poliza`
1. **Alias (dato del módulo):** `data/mail_alias_polizas.xml` — `mail.alias` con `alias_name='polizas'`, `alias_model_id` = `bca.poliza`, `alias_contact='partners'` (**solo remitentes conocidos** — ver §6 seguridad), `alias_defaults` con `{'aseguradora_id': <MetLife>}`.
2. **Override en `models/poliza.py`:**
   - `message_new(msg_dict, custom_values)` — lee los adjuntos PDF de `msg_dict['attachments']`; por cada PDF llama al extractor; construye vals vía el mixin; crea la póliza en `borrador`; adjunta el PDF; programa actividad de revisión (`activity_schedule('mail.mail_activity_data_todo', user_id=<capturista>, summary='Revisar y confirmar póliza extraída de correo')`). Devuelve el/los registros creados.
   - **Robustez del gateway (crítico):** `message_new` **no debe lanzar** ante un PDF malo/ilegible (una excepción rebota el correo). Envolver la extracción en `try/except`; ante fallo o `faltantes` de requeridos: **no crear** póliza inválida, sino registrar en el log, y crear una **actividad de captura manual** (o notificar al buzón del capturista) con el PDF adjunto para intervención humana. Documentar el comportamiento elegido en `Decisiones.md`.
   - `ramo`: se infiere del producto resuelto (como hace `_compute_ramo`); si no se puede inferir para elegir extractor, intentar Vida y GMM y quedarse con el que resuelva los requeridos, o dejar para captura manual.
3. **Config:** `ir.config_parameter` `bca_seguros.alta_pdf_capturista_uid` (usuario destino de la actividad de revisión); default al autor del correo si es interno, o al admin del módulo.

### 4.3 Regla común: nunca auto-confirmar
Ambos canales terminan en `estado='borrador'`. La transición a `activa` (que dispara `_generar_plan_pagos` y crea recibos — irreversible según R-POL-05) es **exclusivamente** el botón Confirmar operado por una persona. Motivo: una extracción errónea activada sola generaría un plan de pagos incorrecto no regenerable.

---

## 5. Seguridad

- **ACL** (`security/ir.model.access.csv`): nuevo modelo transient `bca.wizard.alta.poliza.pdf` → CRUD para `group_bca_operador` y superiores (mismos grupos que pueden crear pólizas). Sin acceso para `group_bca_agente` salvo que el negocio lo pida.
- **Record rules:** la póliza creada respeta las rules existentes de `bca.poliza` (no se añaden nuevas). El agente resuelto define visibilidad.
- **Alias — anti-spoofing (⚠️ importante):** `alias_contact='partners'` para que solo remitentes con `res.partner` conocido creen registros; correos de desconocidos se descartan/bouncan. Como salvaguarda adicional, la póliza siempre nace en `borrador` sin efectos colaterales (no genera recibos), así que un correo malicioso, en el peor caso, crea un borrador que el capturista descarta. Documentar la política de aceptación de remitentes en `Decisiones.md`.
- **Adjuntos:** validar `mimetype`/tamaño del PDF antes de procesar; ignorar adjuntos no-PDF; tope de tamaño configurable para evitar PDFs-bomba.

---

## 6. Archivos a crear / modificar

**Nuevos:**
- `extractors/__init__.py`, `extractors/base.py`, `extractors/metlife_vida.py`, `extractors/metlife_gmm.py`
- `models/poliza_import_mixin.py` (`AbstractModel bca.poliza.import.mixin`)
- `wizards/alta_poliza_pdf.py`
- `views/wizard_alta_poliza_pdf_views.xml`
- `data/mail_alias_polizas.xml`
- `data/config_parameters.xml` → añadir `ocr_umbral_texto`, `alta_pdf_capturista_uid` (o extender el existente)
- `tests/test_extractor_metlife.py`, `tests/test_alta_poliza_pdf.py`
- Carátulas PDF de muestra en `tests/fixtures/` (Vida + GMM) para tests deterministas.

**Modificados:**
- `models/poliza.py` — heredar mixin donde aplique; override `message_new`/`message_update`.
- `wizards/carga_portafolio.py` — heredar `bca.poliza.import.mixin` y **eliminar** los resolvers duplicados (refactor DRY). Cubierto por los tests existentes de portafolio (regresión).
- `models/__init__.py`, `wizards/__init__.py`, `extractors` alta en `__init__.py` raíz.
- `__manifest__.py` — `external_dependencies` (+pdfplumber, pytesseract, pdf2image); `data` (+ vista wizard, + alias, + config); bump `19.0.1.12.0`.
- `Specs/Plan de Desarrollo.md` (Etapa 13), `Specs/Decisiones.md` (D-19…), `Specs/Changelog.md`, `Specs/TESTS_COVERAGE.md`.

---

## 7. Fases (commit + bump por fase)

| Fase | Versión | Nombre | Entregable |
|---|---|---|---|
| A | `19.0.1.12.0` | **Refactor mixin + extractor base** | `bca.poliza.import.mixin`; `carga_portafolio` migrado y verde; `extractors/base.py` + `get_extractor`; tests base con texto simulado |
| B | `19.0.1.12.1` | **Plantillas MetLife Vida/GMM (texto)** | `metlife_vida.py`/`metlife_gmm.py`; anclas calibradas contra carátula real; tests con fixtures PDF |
| C | `19.0.1.12.2` | **Wizard manual (2 fases)** | `alta_poliza_pdf.py` + vista + menú + botón en póliza; previsualizar/crear borrador; ACL |
| D | `19.0.1.12.3` | **Fallback OCR** | detección de PDF sin texto + Tesseract; import perezoso + UserError si falta binario; test con PDF escaneado |
| E | `19.0.1.12.4` | **Intake por correo** | alias `polizas`; `message_new` robusto; actividad de revisión; anti-spoofing; test de gateway |

---

## 8. Tests (obligatorios)

- **Extractor (unitario, sin BD):** texto crudo fijo → `vals` esperados; campos faltantes → aparecen en `faltantes` sin excepción; PDF ilegible total → error controlado; camino texto vs OCR.
- **Wizard manual:** previsualizar no toca BD; crear borrador crea póliza en `borrador` + adjunta PDF; abre form; savepoint aísla fallos.
- **Intake correo:** `message_new` con PDF válido crea borrador + actividad; PDF ilegible NO lanza (no rebota correo) y deja actividad de captura manual; remitente desconocido descartado.
- **No auto-confirma:** póliza creada por ambos canales queda en `borrador` (nunca `activa`).
- **Regresión:** suite de `carga_portafolio` sigue verde tras el refactor del mixin.
- **Ejecutar:** `odoo-bin --test-enable --test-tags BCA_Seguros -i BCA_Seguros`

---

## 9. Checklist Etapa 13
- [ ] **Fase A:** mixin extraído; `carga_portafolio` sin resolvers duplicados y suite de portafolio verde; `get_extractor` con error descriptivo.
- [ ] **Fase B:** anclas MetLife Vida/GMM calibradas contra **carátula real** (quita el `TODO`); fixtures PDF en `tests/`.
- [ ] **Fase C:** wizard previsualiza sin tocar BD; crea borrador + adjunta PDF + abre form; ACL correcta; botón "Alta desde PDF" en póliza.
- [ ] **Fase D:** fallback OCR activo solo si falta capa de texto; `UserError` claro si falta tesseract/poppler; camino reportado.
- [ ] **Fase E:** alias `polizas` operativo; `message_new` no rebota correos ante PDF malo; actividad de revisión asignada; `alias_contact='partners'`.
- [ ] Póliza nunca se auto-confirma (ambos canales → `borrador`).
- [ ] `external_dependencies` declaradas; README con instalación de binarios OCR.
- [ ] Verde `0 failed, 0 error(s)` en Docker local.
- [ ] `Decisiones.md` (D-19 alias/anti-spoofing, D-20 no-auto-confirmar, D-21 fallback OCR opcional) y `Changelog.md` actualizados.

---

## 10. Riesgos y decisiones abiertas
1. **Calibración de anclas (bloqueante):** requiere ≥1 carátula PDF real por ramo. Sin ella, Fase B no cierra.
2. **Variabilidad de layout MetLife:** si emiten varios formatos de carátula, cada uno puede necesitar su juego de anclas (o anclas tolerantes). Evaluar con muestras reales.
3. **Binarios OCR en el server:** confirmar con infra si se instalan Tesseract+Poppler o si el fallback queda deshabilitado (PDF siempre con texto).
4. **Destino de la actividad de revisión:** definir el usuario/grupo capturista por defecto (config param).
5. **Política de remitentes del alias:** confirmar `partners` vs `everyone` con el negocio (seguridad vs comodidad).
