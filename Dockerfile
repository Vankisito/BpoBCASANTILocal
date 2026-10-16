FROM odoo:19

# Odoo 19 image = Debian Bookworm, Python 3.12 con PEP 668 (externally managed).
# Instalar a nivel sistema para que el usuario `odoo` (proceso) lo vea sin trucos.
# pypdf 6.x lo exige BCA_seguros_ocr para extraer texto de carátulas PDF.
RUN pip install --break-system-packages pypdf