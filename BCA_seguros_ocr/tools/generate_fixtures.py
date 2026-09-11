"""Generate .txt fixture files from real PDF carátulas.

Usage:
    pip install pypdf
    python tools/generate_fixtures.py [--pdf-dir RUTA]

Output goes to tests/fixtures/, which is committed to the repo.
"""

from __future__ import annotations

import argparse
import os
import sys

MODULE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURES_DIR = os.path.join(MODULE_ROOT, "tests", "fixtures")

DEFAULT_PDF_DIRS = [
    r"C:\Users\Santi\Desktop\Archivos BCA\polizas\Caratulas",
    "/mnt/extra-addons/Archivos BCA/polizas/Caratulas",
]

PDF_NAMES = [
    "0001420597_Caratula_GM6029.pdf",
    "0000018128_Caratula_GM6029.pdf",
    "0008497462_Caratula_IV6001.pdf",
    "0008495803_Poliza_IV1360.pdf",
    "0008493880_Poliza_IV1360ME.pdf",
    "0008497494_Caratula_IV6001.pdf",
    "0008494374_Caratula_IV6001.pdf",
    "0008496336_Poliza_IV1360ME.pdf",
    "0008497472_Poliza_IV1360ME.pdf",
    "0008495582_Poliza_IV1360ME.pdf",
]


def resolve_pdf_dir(arg: str | None) -> str:
    candidates = [arg] if arg else []
    candidates += DEFAULT_PDF_DIRS
    for p in candidates:
        if p and os.path.isdir(p):
            return p
    raise SystemExit("ERROR: no se encontró directorio de PDFs. Probar: --pdf-dir RUTA")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera fixtures .txt desde PDFs reales."
    )
    parser.add_argument("--pdf-dir", help="Directorio con los PDFs")
    args = parser.parse_args()
    pdf_dir = resolve_pdf_dir(args.pdf_dir)

    # pypdf se importa aquí para validar solo cuando se ejecuta.
    try:
        from pypdf import PdfReader
    except ImportError:
        print("ERROR: pypdf not installed. Run: pip install pypdf")
        sys.exit(1)

    os.makedirs(FIXTURES_DIR, exist_ok=True)
    generated = 0

    for pdf_name in PDF_NAMES:
        pdf_path = os.path.join(pdf_dir, pdf_name)
        if not os.path.exists(pdf_path):
            print(f"  SKIP (not found): {pdf_name}")
            continue

        reader = PdfReader(pdf_path)
        pages_text: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

        txt_name = pdf_name.replace(".pdf", ".txt")
        txt_path = os.path.join(FIXTURES_DIR, txt_name)
        with open(txt_path, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(pages_text))

        poliza = pdf_name.split("_")[0]
        pages = len(reader.pages)
        chars = sum(len(t) for t in pages_text)
        print(f"  OK: {poliza} -> {txt_name} ({pages} pages, {chars} chars)")
        generated += 1

    print(f"\nGenerated {generated}/{len(PDF_NAMES)} fixtures in {FIXTURES_DIR}")


if __name__ == "__main__":
    main()
