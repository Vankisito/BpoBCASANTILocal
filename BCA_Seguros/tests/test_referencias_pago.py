from __future__ import annotations

from datetime import date

from odoo.tests.common import TransactionCase


class TestReferenciasPagoMigracion(TransactionCase):
    """Garantiza que las refs MetLife legacy del contratante se trasladan a
    cada póliza con los valores correctos y sin pisar datos ya capturados."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        Partner = cls.env['res.partner']
        cls.aseguradora = cls.env.ref('BCA_Seguros.partner_metlife')
        cls.holding = Partner.create({'name': 'Holding Refs', 'bca_tipo': 'holding'})
        cls.promotoria = Partner.create({
            'name': 'Promotoría Refs',
            'bca_tipo': 'promotoria',
            'parent_id': cls.holding.id,
        })
        cls.agente = Partner.create({
            'name': 'Agente Refs',
            'bca_tipo': 'agente',
            'parent_id': cls.promotoria.id,
        })
        cls.contratante = Partner.create({'name': 'Contratante Refs'})
        cls.producto_vida = cls.env['product.template'].create({
            'name': 'Vida Refs',
            'bca_es_producto_seguro': True,
            'bca_aseguradora_id': cls.aseguradora.id,
            'bca_ramo': 'vida',
        })
        cls.producto_gmm = cls.env['product.template'].create({
            'name': 'GMM Refs',
            'bca_es_producto_seguro': True,
            'bca_aseguradora_id': cls.aseguradora.id,
            'bca_ramo': 'gmm',
        })
        cls.producto_autos = cls.env['product.template'].create({
            'name': 'Autos Refs',
            'bca_es_producto_seguro': True,
            'bca_aseguradora_id': cls.aseguradora.id,
            'bca_ramo': 'autos',
        })

    def _crear_poliza(self, name: str, producto, **overrides):
        vals = {
            'name': name,
            'aseguradora_id': self.aseguradora.id,
            'producto_id': producto.id,
            'agente_id': self.agente.id,
            'contratante_id': self.contratante.id,
            'fecha_inicio': date(2026, 1, 1),
            'fecha_fin': date(2027, 1, 1),
            'periodicidad': 'anual',
            'prima_anual': 12000.0,
        }
        vals.update(overrides)
        return self.env['bca.poliza'].create(vals)

    def _referencias_legacy(self) -> dict:
        return {
            'bca_ref_prima_basica_trad': 'TRAD-MIG-001',
            'bca_ref_prima_medica': 'MED-MIG-001',
            'bca_fondo_variable': 'FV-MIG-001',
            'bca_fondo_fijo': 'FF-MIG-001',
            'bca_fondo_variable_ppr': 'FV-PPR-MIG-001',
            'bca_fondo_fijo_ppr': 'FF-PPR-MIG-001',
            'bca_fondo_variable_cpea': 'FV-CPEA-MIG-001',
            'bca_fondo_fijo_cpea': 'FF-CPEA-MIG-001',
        }

    def test_migracion_traslada_referencias_por_ramo(self) -> None:
        """Vida recibe TRAD + fondos; GMM recibe médica; autos no recibe nada."""
        vida = self._crear_poliza('POL-MIG-VIDA', self.producto_vida)
        gmm = self._crear_poliza('POL-MIG-GMM', self.producto_gmm)
        autos = self._crear_poliza('POL-MIG-AUTOS', self.producto_autos)
        refs = self._referencias_legacy()
        self.contratante.write(refs)

        self.env['bca.poliza']._migrar_referencias_pago_legacy()

        self.assertEqual(
            vida.bca_ref_prima_basica_trad,
            refs['bca_ref_prima_basica_trad'],
        )
        self.assertEqual(vida.bca_fondo_variable, refs['bca_fondo_variable'])
        self.assertEqual(vida.bca_fondo_fijo, refs['bca_fondo_fijo'])
        self.assertEqual(vida.bca_fondo_variable_ppr, refs['bca_fondo_variable_ppr'])
        self.assertEqual(vida.bca_fondo_fijo_ppr, refs['bca_fondo_fijo_ppr'])
        self.assertEqual(vida.bca_fondo_variable_cpea, refs['bca_fondo_variable_cpea'])
        self.assertEqual(vida.bca_fondo_fijo_cpea, refs['bca_fondo_fijo_cpea'])
        self.assertFalse(vida.bca_ref_prima_medica)

        self.assertEqual(gmm.bca_ref_prima_medica, refs['bca_ref_prima_medica'])
        self.assertFalse(gmm.bca_ref_prima_basica_trad)
        self.assertFalse(gmm.bca_fondo_variable)

        self.assertFalse(autos.bca_ref_prima_basica_trad)
        self.assertFalse(autos.bca_ref_prima_medica)
        self.assertFalse(autos.bca_fondo_variable)

        # Los campos legacy se conservan para rollback.
        self.assertEqual(
            self.contratante.bca_ref_prima_basica_trad,
            refs['bca_ref_prima_basica_trad'],
        )
        self.assertEqual(
            self.contratante.bca_ref_prima_medica,
            refs['bca_ref_prima_medica'],
        )

    def test_migracion_no_sobrescribe_valores_de_poliza(self) -> None:
        """Solo llena campos vacíos: respeta refs ya capturadas en la póliza."""
        vida = self._crear_poliza(
            'POL-MIG-VIDA-PROPIA',
            self.producto_vida,
            bca_ref_prima_basica_trad='TRAD-PROPIA',
            bca_fondo_variable='FV-PROPIO',
        )
        self.contratante.write(self._referencias_legacy())

        self.env['bca.poliza']._migrar_referencias_pago_legacy()

        self.assertEqual(vida.bca_ref_prima_basica_trad, 'TRAD-PROPIA')
        self.assertEqual(vida.bca_fondo_variable, 'FV-PROPIO')
        self.assertEqual(vida.bca_fondo_fijo, 'FF-MIG-001')
