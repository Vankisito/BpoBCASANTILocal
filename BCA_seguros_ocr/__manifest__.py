{
    "name": "BCA Seguros — OCR por Patrones de Carátulas MetLife",
    "version": "19.0.1.2.0",
    "category": "Insurance",
    "summary": "Extracción de carátulas PDF MetLife con regex (sin IA)",
    "description": """
Módulo de extracción de datos de carátulas PDF de pólizas MetLife
usando pypdf + regex. Sin inteligencia artificial.

Soporta dos layouts:
- GMM (Gastos Médicos Mayores): GO-2-025 / GM6029
- Vida Individual: VV-2-008 / IV-1-360 / IV1360 / IV1360ME

Flujo: subir PDF → extraer texto → detectar layout → aplicar regex →
vista previa editable → crear póliza en borrador.
    """,
    "author": "Hábitat Digital",
    "maintainer": ["Hábitat Digital"],
    "website": "https://github.com/Vankisito/BpoBCASANTILocal",
    "license": "LGPL-3",
    "depends": ["BCA_Seguros", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/cron_purga_ocr.xml",
        "security/record_rules.xml",
        "views/bca_ocr_documento_views.xml",
        "views/wizard_ocr_views.xml",
        "views/menu.xml",
    ],
    "external_dependencies": {
        "python": ["pypdf"],
    },
    "installable": True,
    "application": False,
}
