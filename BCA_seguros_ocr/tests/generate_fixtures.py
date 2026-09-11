"""Generate .txt fixture files from real PDF carátulas.

Run INSIDE Docker (pypdf must be installed):
  docker exec -it odoo_dev pip install pypdf
  docker exec -it odoo_dev python /mnt/extra-addons/BCA_seguros_ocr/tests/generate_fixtures.py

Or run locally if pypdf is installed:
  python tests/generate_fixtures.py

PDFs must be in ../Caratulas/ relative to this script.
Output goes to tests/fixtures/.
"""
from __future__ import annotations

import os
import sys

try:
    from pypdf import PdfReader
except ImportError:
    print('ERROR: pypdf not installed. Run: pip install pypdf')
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Host path (Windows) or in-container mount path
_PDF_DIRS = [
    r'C:\Users\Santi\Desktop\Archivos BCA\polizas\Caratulas',
    '/mnt/extra-addons/BCA_seguros_ocr/../Archivos BCA/polizas/Caratulas',
]
PDF_DIR = next((p for p in _PDF_DIRS if os.path.isdir(p)), _PDF_DIRS[0])
FIXTURES_DIR = os.path.join(SCRIPT_DIR, 'fixtures')

PDF_NAMES = [
    '0001420597_Caratula_GM6029.pdf',
    '0000018128_Caratula_GM6029.pdf',
    '0008497462_Caratula_IV6001.pdf',
    '0008495803_Poliza_IV1360.pdf',
    '0008493880_Poliza_IV1360ME.pdf',
    '0008497494_Caratula_IV6001.pdf',
    '0008494374_Caratula_IV6001.pdf',
    '0008496336_Poliza_IV1360ME.pdf',
    '0008497472_Poliza_IV1360ME.pdf',
    '0008495582_Poliza_IV1360ME.pdf',
]


def main() -> None:
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    generated = 0

    for pdf_name in PDF_NAMES:
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        if not os.path.exists(pdf_path):
            print(f'  SKIP (not found): {pdf_name}')
            continue

        reader = PdfReader(pdf_path)
        pages_text: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

        txt_name = pdf_name.replace('.pdf', '.txt')
        txt_path = os.path.join(FIXTURES_DIR, txt_name)
        with open(txt_path, 'w', encoding='utf-8') as fh:
            fh.write('\n\n'.join(pages_text))

        # Extract poliza number for display
        poliza = pdf_name.split('_')[0]
        pages = len(reader.pages)
        chars = sum(len(t) for t in pages_text)
        print(f'  OK: {poliza} → {txt_name} ({pages} pages, {chars} chars)')
        generated += 1

    print(f'\nGenerated {generated}/{len(PDF_NAMES)} fixtures in {FIXTURES_DIR}')


if __name__ == '__main__':
    main()
