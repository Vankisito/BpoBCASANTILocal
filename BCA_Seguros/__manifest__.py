{
    'name': 'BCA Seguros — Gestión de Pólizas y Cobranza',
    'version': '19.0.1.3.0',
    'category': 'Insurance',
    'summary': 'Módulo vertical BCA para pólizas, cobranza, PCA y comisiones',
    'author': 'Hábitat Digital',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'product', 'hr_recruitment', 'crm', 'web'],
    'data': [
        # Seguridad (siempre primero)
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        # Datos iniciales
        'data/sequences.xml',
        'data/partner_categories.xml',
        'data/product_categories.xml',
        'data/hr_jobs.xml',
        'data/aseguradoras_iniciales.xml',
        'data/productos_metlife.xml',
        'data/conductos_metlife.xml',
        'data/factores_metlife_2026.xml',
        'data/config_parameters.xml',
        'data/cron_estatus_pago.xml',
        # Vistas (orden: definir actions y views antes que el menú que las referencia)
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
        'views/hr_applicant_views.xml',
        'views/crm_lead_views.xml',
        'views/conducto_views.xml',
        'views/factor_pca_views.xml',
        'views/poliza_views.xml',
        'views/recibo_views.xml',
        'views/bitacora_views.xml',
        'views/reportes_views.xml',
        'views/wizard_carga_portafolio_views.xml',
        'views/wizard_cobranza_diaria_views.xml',
        # menu.xml siempre último: depende de todas las actions anteriores
        'views/menu.xml',
    ],
    'post_init_hook': 'post_init_hook_bca_seguros',
    'installable': True,
    'application': True,
    # Declarar siempre libs externas (ver Plan §2.4.7): sin esto Odoo instala
    # el módulo aunque la lib no exista y falla en runtime con ImportError.
    'external_dependencies': {
        'python': ['openpyxl'],
    },
}
