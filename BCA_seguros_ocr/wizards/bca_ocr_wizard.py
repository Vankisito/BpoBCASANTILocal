"""OCR wizard for batch PDF upload and processing.

The wizard allows uploading one or more PDFs, processes them through the
OCR pipeline, and shows results.  Each PDF creates a ``bca.ocr.documento``
staging record from which the user can create the final ``bca.poliza``.
"""
from __future__ import annotations

import base64
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BcaOcrWizard(models.TransientModel):
    _name = 'bca.ocr.wizard'
    _description = 'Wizard OCR — Carga de Carátulas MetLife'

    archivo_pdf: bytes = fields.Binary(
        string='Archivo PDF',
        required=True,
    )
    archivo_nombre: str = fields.Char(string='Nombre del Archivo')
    state: str = fields.Selection(
        [('cargar', 'Cargar'), ('resultado', 'Resultado')],
        string='Estado',
        default='cargar',
    )

    def action_procesar(self) -> dict:
        """Process the uploaded PDF through the OCR pipeline."""
        self.ensure_one()

        if not self.archivo_pdf:
            raise UserError(_('Debe adjuntar un archivo PDF.'))

        nombre = self.archivo_nombre or 'documento.pdf'

        # Create staging record
        Doc = self.env['bca.ocr.documento']
        doc = Doc.create({
            'archivo_pdf': self.archivo_pdf,
            'archivo_nombre': nombre,
        })

        # Extract
        try:
            doc.action_extraer()
        except Exception:
            _logger.exception('OCR extraction failed')
            doc.write({
                'estado': 'error',
                'error_mensaje': _(
                    'No se pudo procesar el PDF. '
                    'Verifique que el archivo sea un PDF válido de una carátula '
                    'MetLife, o intente con otro archivo.'
                ),
            })

        # Open the staging form directly — user reviews & corrects data
        view_form = self.env.ref('BCA_seguros_ocr.view_ocr_documento_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Revisar Extracción OCR'),
            'res_model': 'bca.ocr.documento',
            'res_id': doc.id,
            'view_mode': 'form',
            'view_id': view_form.id,
            'target': 'current',
        }
