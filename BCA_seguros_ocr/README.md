# BCA_seguros_ocr

Módulo Odoo 19 para extraer datos de carátulas/pólizas PDF de **MetLife** (GMM y
Vida Individual) y crear pólizas `bca.poliza` en borrador listas para revisión y
confirmación.

**Sin IA**: la extracción usa `pypdf` (texto del PDF) + expresiones regulares.
Determinista, sin costo, sin datos enviados a servicios externos.

---

## 1. Requisitos

| Requisito | Detalle |
|---|---|
| Odoo | 19.0 (APIs web de Odoo 19, vistas `list`/`form`) |
| Python | 3 (imagen Odoo 19 ya lo trae) |
| `pypdf` | >= 6.0 (instalado en la imagen del contenedor) |
| Dependencias Odoo | `BCA_Seguros` (modelos `bca.poliza`, `bca_tipo` en partners), `mail` |
| Formatos soportados | Carátulas MetLife: **GMM** (`GO-2-025` / `GM6029`) y **Vida Individual** (`VV-2-008` / `IV-1-360` / `IV1360` / `IV1360ME`) |

Los PDFs de prueba viven localmente en
`C:\Users\Santi\Desktop\Archivos BCA\polizas\Caratulas`.

---

## 2. Instalación / actualización

En el contenedor (CLI):

```bash
# Instalar
docker exec odoo_dev odoo -d bca_clean -i BCA_seguros_ocr --stop-after-init \
  --addons-path=/mnt/extra-addons --db_host=db --db_port=5432 \
  --db_user=odoo --db_password=odoo

# Actualizar (tras editar módulo)
docker exec odoo_dev odoo -d bca_clean -u BCA_seguros_ocr --stop-after-init \
  --addons-path=/mnt/extra-addons --db_host=db --db_port=5432 \
  --db_user=odoo --db_password=odoo

# Reiniciar servidor
docker restart odoo_dev
```

### 2.1 Instalar pypdf (requisito previo)

La imagen oficial de Odoo 19 **no incluye `pypdf`**. Sin él el módulo falla al
iniciar:

```
ModuleNotFoundError: No module named 'pypdf'
```

O aparece al subir el PDF:

```
ImportError: pypdf no está instalado. Ejecute: pip install --break-system-packages pypdf
```

La imagen es Debian Bookworm + Python 3.12 con **PEP 668** (externally managed
environment), así que `pip install` simple falla con:

```
error: externally-managed-environment
× This environment is externally managed
```

**Solución recomendada — Dockerfile** (ya aplicado en este proyecto, `Odoo 19 docker/Dockerfile`):

```dockerfile
FROM odoo:19
# Debian Bookworm + Python 3.12 + PEP 668: --break-system-packages es obligatorio.
RUN pip install --break-system-packages pypdf
```

Después `docker compose up --build`.

**Solución alternativa — sin Dockerfile** (instalar directo en el contenedor):

```bash
# Entrar al contenedor como root
docker exec -u root -it odoo_dev bash

# Dentro del contenedor:
pip install --break-system-packages pypdf

# Salir
exit

# Reiniciar para que Odoo lo vea
docker restart odoo_dev
```

> **⚠️ Importante**: esta alternativa funciona pero el paquete **se pierde al
> reconstruir la imagen** (`docker compose up --build`). Siempre es mejor
> incluirlo en el Dockerfile como se muestra arriba.

---

## 3. Estructura del módulo

```
BCA_seguros_ocr/
├── __manifest__.py
├── models/
│   └── bca_ocr_documento.py    # Modelo bca.ocr.documento (staging + acciones)
├── extractors/
│   ├── __init__.py
│   ├── base.py                 # detectar_layout, normalizar_monto
│   ├── metlife_gmm.py          # Extractor GMM
│   └── metlife_vida.py         # Extractor Vida Individual
├── wizards/
│   └── bca_ocr_wizard.py       # Wizard de subida de PDF
├── views/
│   ├── bca_ocr_documento_views.xml
│   ├── wizard_ocr_views.xml
│   └── menu.xml
├── security/
│   └── ir.model.access.csv     # ACLs por grupo
├── tests/
│   ├── test_extractors.py      # 22 unit tests sobre fixtures (sin Odoo)
│   ├── validate_extractors.py  # 10/10 contra PDFs reales (sin Odoo)
│   ├── generate_fixtures.py    # Regenera fixtures .txt (requiere PDFs)
│   └── fixtures/*.txt          # Texto crudo de los 10 PDFs reales
└── README.md
```

### Modelo `bca.ocr.documento`

Campos principales:

| Campo | Tipo | Descripción |
|---|---|---|
| `archivo_pdf` | Binary | PDF subido por el usuario |
| `archivo_nombre` | Char | Nombre original del archivo |
| `estado` | Selection | `nuevo` → `extraido` → `creado` (o `error`) |
| `texto_extraido` | Text | Texto crudo del PDF (pypdf) |
| `layout_detectado` | Char | `gmm` / `vida` / `desconocido` |
| `error_mensaje` | Text | Motivo de `estado == 'error'` |
| `poliza_numero` | Char | Nº de póliza (de la carátula) |
| `producto_pdf` | Char | Nombre del producto tal como aparece en el PDF |
| `agente_clave` | Char | Clave de agente (de la carátula) |
| `contratante_nombre` | Char | Contratante |
| `asegurado_nombre` | Char | Asegurado |
| `fecha_emision` / `fecha_inicio` / `fecha_fin` | Date | Fechas de la póliza |
| `prima_monto` | Monetary | Prima anual |
| campos GMM | | `deducible`, `coaseguro`, `iva`, `recargo_frac`, `plan`, `nivel_hospitalario` |
| campos Vida | | `suma_asegurada`, `beneficiario`, `beneficiario_parentesco` |
| `poliza_id` | Many2one `bca.poliza` | Póliza creada |

Métodos / botones:

| Botón | Método | Qué hace |
|---|---|---|
| Procesar (wizard) | `BcaOcrWizard.action_procesar` | Extrae texto + layout, corre extractor, guarda staging, abre el form `bca.ocr.documento` con `view_id` forzado |
| Extraer Datos (re-extracción) | `BcaOcrDocumento.action_extraer` | Re-ejecuta extracción |
| Ver Texto | `action_ver_texto` | Dialog con el texto crudo extraído |
| **Crear Póliza** | `action_crear_poliza` | Resuelve aseguradora/agente/producto/contratante y crea `bca.poliza` borrador |
| Abrir Póliza | `action_abrir_poliza` | Abre la `bca.poliza` ya creada |

### Resolución de referencias (`helpers.py`)

| Referencia | Regla | Si falla |
|---|---|---|
| Aseguradora | Partner `bca_tipo='aseguradora'` nombre `ilike 'metlife'` | UserError claro |
| Agente | `res.partner.agente.aseguradora` por `clave_agente` (+ tolerant lookup de ceros a la izquierda) | Warning, campo queda vacío, usuario corrige |
| Producto | 1) nombre exacto → 2) `bca_nombre_archivo_aseguradora` → 3) `ilike` nombre. Filtros: `bca_es_producto_seguro=True`, `bca_aseguradora_id=MetLife`, ramo | **UserError claro**: explica que el producto no está en catálogo y cómo resolverlo |
| Contratante/Asegurado | `find_or_create_partner` (por RFC → nombre → nombre normalizado → crea) | Crea partner si no existe |

> **Importante**: `bca.poliza` requiere `producto_id`, `agente_id`, `fecha_inicio`,
> `fecha_fin`. Si el producto no se resuelve, la creación se aborta con un
> mensaje claro ANTES de intentar crear (nunca llega al error técnico de
> constraint NOT NULL). El usuario debe crear el producto o corregir el nombre
> en el catálogo.

---

## 4. Manual de uso

### USUARIO: crear una póliza desde PDF

1. **Menú**: *Pólizas → OCR Carátulas → Subir Carátula* (o el menú OCR configurado).
2. **Subir PDF**: clic en *Subir archivo*, elige el PDF de la carátula MetLife,
   clic **Procesar**.
3. **Revisar datos**: se abre automáticamente el formulario con los datos
   extraídos. Verifica que sean correctos (póliza, fechas, prima, contratante).
   - Botón **Ver Texto** (parte superior): muestra el texto crudo del PDF,
     útil si algún dato sale mal.
4. **Crear Póliza**: clic en el botón **Crear Póliza** (arriba, junto a
   "Ver Texto"). Confirma el diálogo.
   - Si el producto no existe en el catálogo, aparece un error claro:
     crea el producto en *Productos* o corrige el nombre (ver sección de
     errores comunes).
5. **Póliza en borrador**: el sistema abre la `bca.poliza` creada. Revisa y
   completa los campos obligatorios que hayan quedado vacíos (agente, fechas)
   y procesa el borrador como una póliza normal.

### ADM (solucionar el error de producto)

Si al crear la póliza aparece:

> *No se encontró el producto "METALIFE EDUCACIÓN" (ramo vida) en el catálogo.*

El nombre del PDF no coincide con ningún producto. Dos opciones:

- **A. Crear el producto** en *Ventas → Productos*: activa "Es producto de
  seguro", asigna aseguradora MetLife (id/partner tipo aseguradora), ramo
  (`vida` o `gmm`) y el nombre exacto.
- **B. Mapear el nombre**: en un producto existente (p. ej. `MetLife
  EducaLife`), rellena el campo *Nombre archivo aseguradora* con
  `METALIFE EDUCACIÓN` (texto tal cual del PDF). El resolutor matchea por ese
  campo antes que por nombre.

---

## 5. Pruebas

Dos suites **sin Odoo** (no requieren contenedor):

```bash
# Unit tests (22) — regex/parseo sobre fixtures de texto
python tests/test_extractors.py

# Validación (10/10) — PDFs reales comparados contra golden data
# Requiere pypdf y la carpeta C:\Users\Santi\Desktop\Archivos BCA\polizas\Caratulas
python tests/validate_extractors.py
```

Estado actual: **22/22** unit tests, **10/10** validación (2 GMM + 8 Vida).

---

## 6. Historial de cambios

| Fecha | Cambio |
|---|---|
| 2026-09-11 | Fix botón "Crear Póliza": stat button en `button_box` + `view_id` forzado en el wizard (elimina ambigüedad entre la vista form y la de texto) |
| 2026-09-11 | Fix "Abrir Póliza": invisible contradictorio corregido; nuevo método `action_abrir_poliza` |
| 2026-09-11 | Error de producto amigable: se aborta con `UserError` claro antes del constraint NOT NULL de `bca.poliza` |
| 2026-09-11 | Wizard simplificado: `action_procesar` abre directo el form `bca.ocr.documento`; eliminados reporte HTML y pantallas intermedias |
| 2026-09-11 | Compat Odoo 19: `<tree>`→`<list>`; search view sin `expand`/`string` en `<group>` |
| 2026-09-11 | Import `mail.activity.mixin` + dependencia `mail` |
| 2026-09-11 | `prima_monto` corregido (antes `prima_total` inexistente) |
| 2026-09-11 | pypdf instalado en `Dockerfile` (`--break-system-packages`) |

---

## 7. Limitaciones conocidas

- Solo MetLife (GMM + Vida Individual). Otros formatos → `estado='error'` con
  mensaje "No se reconoce el formato".
- `helpers.py:resolver_producto` requiere que la carátula y el catálogo usen
  nombres alineados (o el campo *Nombre archivo aseguradora*).
- El módulo no valida ni confirma la póliza: solo la crea en borrador.

---

## 8. Errores comunes al instalar

### `ModuleNotFoundError: No module named 'pypdf'`

Odoo 19 Docker **no trae pypdf**. El módulo lo necesita para leer los PDFs.

```bash
# Error que sale al iniciar Odoo o al subir un PDF:
ModuleNotFoundError: No module named 'pypdf'
```

**Solución**: agregar `pypdf` en el `Dockerfile` (ver sección 2.1).

### `error: externally-managed-environment` (PEP 668)

La imagen Odoo 19 es Debian Bookworm + Python 3.12 con PEP 668 activado.
`pip install pypdf` normal falla:

```bash
# ❌ No funciona
pip install pypdf

# ✅ Funciona — permite instalar a nivel sistema
pip install --break-system-packages pypdf
```

**Solución**: usar `--break-system-packages` siempre, tanto en el Dockerfile
como al instalar manualmente dentro del contenedor (ver sección 2.1).

### La póliza no se crea: "No se encontró el producto"

El nombre del producto en el PDF no coincide con el catálogo. Ejemplo real:
el PDF dice `"METALIFE EDUCACIÓN"` pero en Odoo el producto se llama
`MetLife EducaLife`. Ver sección 5.1 (ADM) para resolverlo.