# Copyright (C) 2018 Florent Mirieu (<https://github.com/fmdl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestWizardImportZpl2(TransactionCase):
    def setUp(self):
        super(TestWizardImportZpl2, self).setUp()
        self.label = self.env['printing.label.zpl2'].create({
            'name': 'ZPL II Label',
            'model_id': self.env.ref('base.model_res_partner').id,
        })

    def test_open_wizard(self):
        """ open wizard from label"""
        res = self.label.import_zpl2()
        self.assertEqual(
            res.get('context').get('default_label_id'),
            self.label.id)

    def test_wizard_import_zpl2(self):
        """ Import ZPL2 from wizard """
        zpl_data = ("^XA\n"
                    "^CI28\n"
                    "^LH0,0\n"
                    "^CF0\n"
                    "^CFA,10\n"
                    "^CFB,10,10\n"
                    "^FO10,10^A0N,30,30^FDTEXT^FS\n"
                    "^BY2,3.0^FO600,60^BCN,30,N,N,N"
                    "^FDAJFGJAGJVJVHK^FS\n"
                    "^FO10,40^A0N,20,40^FB150,2,1,J,0^FDTEXT BLOCK^FS\n"
                    "^FO300,10^GC100,3,B^FS\n"
                    "^FO10,200^GB200,200,100,B,0^FS\n"
                    "^FO10,60^GFA,16.0,16.0,2.0,"
                    "b'FFC0FFC0FFC0FFC0FFC0FFC0FFC0FFC0'^FS\n"
                    "^FO10,200^GB300,100,6,W,0^FS\n"
                    "^BY2,3.0^FO300,10^B1N,N,30,N,N^FD678987656789^FS\n"
                    "^BY2,3.0^FO300,70^B2N,30,Y,Y,N^FD567890987768^FS\n"
                    "^BY2,3.0^FO300,120^B3N,N,30,N,N^FD98765456787656^FS\n"
                    "^BY2,3.0^FO300,200^BQN,2,5,Q,7"
                    "^FDMM,A876567897656787658654645678^FS\n"
                    "^BY2,3.0^FO400,250^BER,40,Y,Y^FD9876789987654567^FS\n"
                    "^BY2,3.0^FO350,250^B7N,20,0,0,0,N^FD8765678987656789^FS\n"
                    "^BY2,3.0^FO700,10^B9N,20,N,N,N^FD87657890987654^FS\n"
                    "^BY2,3.0^FO600,200^B4N,50,N^FD7654567898765678^FS\n"
                    "^BY2,3.0^FO600,300^BEN,50,Y,Y^FD987654567890876567^FS\n"
                    "^FO300,300^AGI,50,50^FR^FDINVERTED^FS\n"
                    "^BY2,3.0^FO700,200^B8,50,N,N^FD987609876567^FS\n"
                    "^JUR\n"
                    "^XZ")

        vals = {'label_id': self.label.id,
                'delete_component': True,
                'data': zpl_data}
        wizard = self.env['wizard.import.zpl2'].create(vals)
        wizard.import_zpl2()
        self.assertEqual(
            18,
            len(self.label.component_ids))

    def test_wizard_import_zpl2_add(self):
        """ Import ZPL2 from wizard ADD"""
        self.env['printing.label.zpl2.component'].create({
            'name': 'ZPL II Label',
            'label_id': self.label.id,
            'data': '"data"',
            'sequence': 10})
        zpl_data = ("^XA\n"
                    "^CI28\n"
                    "^LH0,0\n"
                    "^FO10,10^A0N,30,30^FDTEXT^FS\n"
                    "^JUR\n"
                    "^XZ")

        vals = {'label_id': self.label.id,
                'delete_component': False,
                'data': zpl_data}
        wizard = self.env['wizard.import.zpl2'].create(vals)
        wizard.import_zpl2()
        self.assertEqual(
            2,
            len(self.label.component_ids))
