.. image:: https://img.shields.io/badge/odoo-19.0-blue
   :target: https://github.com/Vankisito/BpoBCASANTILocal
   :alt: Odoo 19.0

.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/lgpl-3.0
   :alt: License: LGPL-3

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit enabled

BCA seguros OCR
===============

Módulo Odoo 19 para extraer datos de carátulas/pólizas PDF de **MetLife**
(GMM y Vida Individual) y crear pólizas ``bca.poliza`` en borrador listas
para revisión y confirmación.

**Sin IA**: la extracción usa ``pypdf`` (texto del PDF) + expresiones
regulares. Determinista, sin costo, sin datos enviados a servicios externos.

Instalación
-----------

Requisitos
~~~~~~~~~~

-  Odoo 19.0
-  Python 3 (imagen Odoo 19 lo trae)
-  ``pypdf`` >= 6.0 (instalado en la imagen del contenedor)
-  Dependencias Odoo: ``BCA_Seguros`` (modelos ``bca.poliza``, ``bca_tipo``
   en partners) y ``mail``
-  Formatos soportados: carátulas MetLife **GMM** (``GO-2-025`` / ``GM6029``)
   y **Vida Individual** (``VV-2-008`` / ``IV-1-360`` / ``IV1360`` /
   ``IV1360ME``)

Los PDFs de prueba viven localmente en
``C:\Users\Santi\Desktop\Archivos BCA\polizas\Caratulas``.

Instalar / actualizar
~~~~~~~~~~~~~~~~~~~~~

En el contenedor (CLI)::

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

Instalar pypdf (requisito previo)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La imagen oficial de Odoo 19 **no incluye ``pypdf``**. Sin él el módulo
falla al iniciar::

    ModuleNotFoundError: No module named 'pypdf'

La imagen es Debian Bookworm + Python 3.12 con **PEP 668** (externally
managed environment); ``pip install`` simple falla con
``error: externally-managed-environment``.

**Solución recomendada — Dockerfile** (ya aplicado en este proyecto)::

    FROM odoo:19
    # Debian Bookworm + Python 3.12 + PEP 668: --break-system-packages es obligatorio.
    RUN pip install --break-system-packages pypdf

Después ``docker compose up --build``.

**Solución alternativa — directo en el contenedor**: usar siempre
``pip install --break-system-packages pypdf``. Ojo: el paquete **se pierde
al reconstruir la imagen**; mejor incluirlo en el Dockerfile.

Estructura del módulo
---------------------

::

    BCA_seguros_ocr/
    ├── __manifest__.py
    ├── models/
    │   └── bca_ocr_documento.py    # Modelo bca.ocr.documento (staging + acciones)
    ├── extractors/
    │   ├── __init__.py
    │   ├── base.py                 # detectar_layout, normalizar_monto, MESES_ES
    │   ├── metlife_gmm.py          # Extractor GMM
    │   └── metlife_vida.py         # Extractor Vida Individual
    ├── ocr_engines/
    │   ├── __init__.py
    │   ├── base.py                 # interfaz ExtractEngine
    │   └── pypdf_engine.py         # implementación con pypdf
    ├── wizards/
    │   └── bca_ocr_wizard.py       # Wizard de subida de PDF
    ├── views/
    │   ├── bca_ocr_documento_views.xml
    │   ├── wizard_ocr_views.xml
    │   └── menu.xml
    ├── security/
    │   └── ir.model.access.csv     # ACLs por grupo
    ├── tests/
    │   ├── test_extractors.py      # unit tests sobre fixtures
    │   └── fixtures/*.txt          # Texto crudo de los PDFs reales
    ├── tools/
    │   ├── validate_extractors.py  # Valida contra PDFs reales (golden data)
    │   └── generate_fixtures.py    # Regenera fixtures .txt (requiere PDFs)
    ├── i18n/
    │   └── BCA_seguros_ocr.pot
    └── README.rst

Modelo ``bca.ocr.documento``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Campos principales:

-  ``archivo_pdf`` (Binary) — PDF subido por el usuario
-  ``archivo_nombre`` (Char) — nombre original del archivo
-  ``estado`` (Selection) — ``nuevo`` → ``extraido`` → ``creado`` (o ``error``)
-  ``texto_extraido`` (Text) — texto crudo del PDF (pypdf)
-  ``layout_detectado`` (Selection) — ``gmm`` / ``vida`` / ``desconocido``
-  ``error_mensaje`` (Text) — motivo de ``estado == 'error'``
-  ``poliza_numero`` (Char) — nº de póliza (de la carátula)
-  ``producto_pdf`` (Char) — nombre del producto tal como aparece en el PDF
-  ``agente_clave`` (Char) — clave de agente (de la carátula)
-  ``contratante_nombre`` / ``asegurado_nombre`` (Char)
-  ``fecha_emision`` / ``fecha_inicio`` / ``fecha_fin`` (**Date**)
-  ``prima_monto`` (Monetary) — prima anual
-  Campos GMM — ``deducible``, ``coaseguro``, ``iva``, ``recargo_frac``,
   ``plan``, ``nivel_hospitalario``
-  Campos Vida — ``suma_asegurada``, ``beneficiarios_texto``
-  ``poliza_id`` (Many2one ``bca.poliza``) — póliza creada

Acciones / botones:

-  **Procesar** (wizard) — ``BcaOcrWizard.action_procesar``: extrae texto +
   layout, corre el extractor, guarda staging y abre el form
   ``bca.ocr.documento``.
-  **Extraer Datos** — ``BcaOcrDocumento.action_extraer``: re-ejecuta la
   extracción.
-  **Ver Texto** — ``action_ver_texto``: diálogo con el texto crudo
   extraído.
-  **Crear Póliza** — ``action_crear_poliza``: resuelve
   aseguradora/agente/producto/contratante y crea ``bca.poliza`` borrador.
-  **Abrir Póliza** — ``action_abrir_poliza``: abre la ``bca.poliza`` ya
   creada.

Resolución de referencias (``helpers.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **Aseguradora** — partner ``bca_tipo='aseguradora'`` nombre
   ``ilike 'metlife'``. Si falla: ``UserError`` claro.
-  **Agente** — ``res.partner.agente.aseguradora`` por ``clave_agente``
   (con lookup tolerante de ceros a la izquierda). Si falla: ``UserError``
   claro explicando cómo dar de alta al agente.
-  **Producto** — 1) nombre exacto → 2) ``bca_nombre_archivo_aseguradora``
   → 3) ``ilike`` nombre. Filtros: ``bca_es_producto_seguro=True``,
   ``bca_aseguradora_id=MetLife``, ramo. Si falla: ``UserError`` claro.
-  **Contratante/Asegurado** — ``find_or_create_partner`` (por RFC →
   nombre → nombre normalizado → crea).

.. note::
   ``bca.poliza`` requiere ``producto_id``, ``agente_id``, ``fecha_inicio``
   y ``fecha_fin``. Si el producto o el agente no se resuelven, la creación
   se aborta con un mensaje claro ANTES del constraint NOT NULL.

Manual de uso
-------------

Crear una póliza desde PDF
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Menú *Pólizas → OCR Carátulas → Subir Carátula*.
2. Subir el PDF de la carátula MetLife y clic en **Procesar**.
3. Revisar los datos extraídos en el formulario. Botón **Ver Texto** para
   depurar extracciones malas.
4. Clic en **Crear Póliza** y confirmar el diálogo.
5. La ``bca.poliza`` en borrador se abre; completar lo que haya quedado
   vacío y procesarla como póliza normal.

Resolver errores de producto / agente
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Producto no encontrado: el nombre del PDF no coincide con el catálogo.
Opciones: **crear** el producto (con *Es producto de seguro*, aseguradora
MetLife y ramo) o **mapear** el nombre en el campo *Nombre archivo
aseguradora* de un producto existente.

Agente no encontrado: la clave no está registrada. Opciones: **registrar**
el contacto (tipo *Agente*, vinculado a MetLife con ``clave_agente``) o
**corregir** la clave extraída en el staging antes de crear la póliza.

Pruebas
-------

Unit tests de los extractores (corren dentro del runner de Odoo, sin
dependencia de ``pypdf``)::

    odoo --test-enable --test-tags '/BCA_seguros_ocr' -u BCA_seguros_ocr --stop-after-init

Validación contra PDFs reales (golden data, requiere ``pypdf`` y la carpeta
``C:\Users\Santi\Desktop\Archivos BCA\polizas\Caratulas``)::

    python tools/validate_extractors.py

Estado actual: **22 unit tests** (fixtures) y **10/10** validación
(2 GMM + 8 Vida).

Historial de cambios
--------------------

-  2026-09-12 — Alineación OCA: fechas ``fields.Date``, lint pre-commit,
  scripts dev movidos a ``tools/``, ``README.rst``, ``i18n``,
  metadata del manifest.
-  2026-09-11 — Errores de PDF amigables (``PdfInvalidoError`` /
  ``PdfEncriptadoError``).
-  2026-09-11 — Error de agente/producto amigable con ``UserError`` claro.
-  2026-09-11 — Fix botones "Crear Póliza" y "Abrir Póliza".
-  2026-09-11 — Compat Odoo 19 (``<list>``, search view).
-  2026-09-11 — ``mail.activity.mixin`` + dependencia ``mail``.
-  2026-09-11 — ``pypdf`` en Dockerfile (``--break-system-packages``).

Limitaciones conocidas
----------------------

-  Solo MetLife (GMM + Vida Individual). Otros formatos → ``estado='error'``
   con mensaje "No se reconoce el formato".
-  ``resolver_producto`` requiere que la carátula y el catálogo usen nombres
   alineados (o el campo *Nombre archivo aseguradora*).
-  El módulo no valida ni confirma la póliza: solo la crea en borrador.
