"""Standalone validation script — run outside Odoo.

Tests the extractors against the real PDFs and compares with golden data.

Usage:
    pip install pypdf
    python tools/validate_extractors.py [--pdf-dir RUTA]
"""

from __future__ import annotations

import argparse
import os
import sys
import time

MODULE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, MODULE_ROOT)

from extractors.base import detectar_layout  # noqa: E402
from extractors.metlife_gmm import MetlifeGmmExtractor  # noqa: E402
from extractors.metlife_vida import MetlifeVidaExtractor  # noqa: E402

DEFAULT_PDF_DIR = r"C:\Users\Santi\Desktop\Archivos BCA\polizas\Caratulas"

# ---------------------------------------------------------------------------
# Golden data
# ---------------------------------------------------------------------------
GMM_EXPECTED = {
    "0001420597": {
        "poliza_numero": "0001420597",
        "contratante_nombre": "JOSEMILIO RAMOS LOPEZ",
        "producto_pdf": "GASTOS MEDICOS MEDICALIFE FAM.",
        "agente_clave": "074887",
        "periodicidad": "semestral",
        "prima_total": 54119.62,
        "prima_neta": 43418.12,
        "iva": 7464.78,
        "recargo_frac": 1736.72,
        "deducible": 52000.0,
        "coaseguro": 0.10,
    },
    "0000018128": {
        "poliza_numero": "0000018128",
        "contratante_nombre": "JORGE ALEJANDRO ALVAREZ ZAVALZA",
        "producto_pdf": "PRIMORDIAL",
        "agente_clave": "073753",
        "periodicidad": "mensual",
        "prima_total": 4617.68,
        "prima_neta": 3600.0,
        "iva": 636.88,
        "recargo_frac": 280.80,
    },
}

VIDA_EXPECTED = {
    "8497462": {
        "poliza_numero": "8497462",
        "contratante_nombre": "PATRICIA LEAL CARREON",
        "producto_pdf": "TEMPOLIFE",
        "agente_clave": "74570",
        "periodicidad": "anual",
        "prima_anual": 26551.50,
        "suma_asegurada": 100000.0,
        "rfc": "LECP6607118I1",
        "num_beneficiarios": 3,
    },
    "8495803": {
        "poliza_numero": "8495803",
        "contratante_nombre": "VERONICA MARIA MARTINEZ MENDEZ",
        "producto_pdf": "FLEXI LIFE INVERSION",
        "agente_clave": "73110",
        "periodicidad": "anual",
        "prima_anual": 445.90,
        "suma_asegurada": 0.0,
        "num_beneficiarios": 2,
    },
    "8493880": {
        "poliza_numero": "8493880",
        "contratante_nombre": "RUTH LOPEZ SALAZAR",
        "producto_pdf": "METALIFE MUJER",
        "agente_clave": "74845",
        "periodicidad": "anual",
        "prima_anual": 66999.98,
        "suma_asegurada": 2232685.0,
        "num_beneficiarios": 1,
    },
    "8497494": {
        "poliza_numero": "8497494",
        "contratante_nombre": "ANA LILIA SANCHEZ QUIROZ",
        "producto_pdf": "TOTALIFE",
        "agente_clave": "73801",
        "periodicidad": "anual",
        "prima_anual": 54326.0,
        "suma_asegurada": 0.0,
        "num_beneficiarios": 2,
    },
    "8494374": {
        "poliza_numero": "8494374",
        "contratante_nombre": "MOISES PEREYRA MENESES",
        "producto_pdf": "VIDA INDIVIDUAL",
        "agente_clave": "74511",
        "periodicidad": "mensual",
        "prima_anual": 42963.96,
        "suma_asegurada": 780000.0,
        "num_beneficiarios": 1,
    },
    "8496336": {
        "poliza_numero": "8496336",
        "contratante_nombre": "JOSE PABLO TORRES MENDOZA",
        "producto_pdf": "METALIFE EDUCACIÓN",
        "agente_clave": "73801",
        "periodicidad": "anual",
        "prima_anual": 68603.79,
        "suma_asegurada": 2145755.0,
        "num_beneficiarios": 1,
    },
    "8497472": {
        "poliza_numero": "8497472",
        "contratante_nombre": "MARIANNE HUGUES BARRAGAN",
        "producto_pdf": "METALIFE RETIRO",
        "agente_clave": "73753",
        "periodicidad": "mensual",
        "prima_anual": 24587.39,
        "suma_asegurada": 1026850.0,
        "num_beneficiarios": 3,
    },
    "8495582": {
        "poliza_numero": "8495582",
        "contratante_nombre": "DEFENIX CARTONES SA DE CV",
        "producto_pdf": "METALIFE TU FUTURO",
        "agente_clave": "74001",
        "periodicidad": "mensual",
        "prima_anual": 22800.0,
        "suma_asegurada": 0.0,
        "num_beneficiarios": 1,
    },
}

GMM_PDFS = ["0001420597_Caratula_GM6029.pdf", "0000018128_Caratula_GM6029.pdf"]
VIDA_PDFS = [
    "0008497462_Caratula_IV6001.pdf",
    "0008495803_Poliza_IV1360.pdf",
    "0008493880_Poliza_IV1360ME.pdf",
    "0008497494_Caratula_IV6001.pdf",
    "0008494374_Caratula_IV6001.pdf",
    "0008496336_Poliza_IV1360ME.pdf",
    "0008497472_Poliza_IV1360ME.pdf",
    "0008495582_Poliza_IV1360ME.pdf",
]


def extract_text(pdf_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def compare(poliza: str, data: dict, expected: dict, errors: list[str]) -> None:
    for key, exp_val in expected.items():
        act_val = data.get(key)
        if isinstance(exp_val, float):
            if act_val is None or abs(act_val - exp_val) > 0.02:
                errors.append(f"  {poliza}.{key}: expected {exp_val}, got {act_val}")
        elif act_val != exp_val:
            errors.append(f"  {poliza}.{key}: expected {exp_val!r}, got {act_val!r}")


def run(pdf_dir: str) -> None:
    gmm_extractor = MetlifeGmmExtractor()
    vida_extractor = MetlifeVidaExtractor()

    total = 0
    passed = 0
    errors: list[str] = []
    start = time.time()

    for pdf_name in GMM_PDFS:
        pdf_path = os.path.join(pdf_dir, pdf_name)
        if not os.path.exists(pdf_path):
            errors.append(f"MISSING: {pdf_name}")
            continue
        poliza = pdf_name.split("_")[0]
        total += 1
        text = extract_text(pdf_path)
        layout = detectar_layout(text)
        if layout != "gmm":
            errors.append(f"{poliza}: layout detected as {layout}, expected gmm")
            continue
        data = gmm_extractor.extract(text)
        before = len(errors)
        compare(poliza, data, GMM_EXPECTED[poliza], errors)
        if len(errors) == before:
            passed += 1
            print(f"  PASS  {poliza} (GMM)")

    for pdf_name in VIDA_PDFS:
        pdf_path = os.path.join(pdf_dir, pdf_name)
        if not os.path.exists(pdf_path):
            errors.append(f"MISSING: {pdf_name}")
            continue
        poliza = pdf_name.split("_")[0].lstrip("0")
        total += 1
        text = extract_text(pdf_path)
        layout = detectar_layout(text)
        if layout != "vida":
            errors.append(f"{poliza}: layout detected as {layout}, expected vida")
            continue
        data = vida_extractor.extract(text)
        before = len(errors)
        compare(poliza, data, VIDA_EXPECTED[poliza], errors)
        if len(errors) == before:
            passed += 1
            print(f"  PASS  {poliza} (Vida)")

    elapsed = time.time() - start

    print(f'\n{"=" * 60}')
    print(f"Results: {passed}/{total} passed in {elapsed:.2f}s")
    if errors:
        print(f"\nFAILED ({len(errors)} errors):")
        for e in errors:
            print(e)
        sys.exit(1)
    print("\nAll tests passed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Valida extractores contra PDFs reales."
    )
    parser.add_argument(
        "--pdf-dir", default=DEFAULT_PDF_DIR, help="Directorio con los PDFs"
    )
    args = parser.parse_args()
    run(args.pdf_dir)
