# -*- coding: utf-8 -*-
# Copyright 2016 ADHOC SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

xmlid_renames = [
    (
        'base_report_to_printer.res_groups_printingprintoperator0',
        'base_report_to_printer.printing_server_group_manager',
    ),
    (
        'base_report_to_printer.ir_model_access_printingprintergroup1',
        'base_report_to_printer.printing_printer_group_manager',
    ),
    (
        'base_report_to_printer.ir_model_access_printing_action',
        'base_report_to_printer.printing_action_group_manager',
    ),
    (
        'base_report_to_printer.ir_model_access_printingreportxmlaction',
        'base_report_to_printer.printing_report_xml_action_group_manager',
    ),
]


@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_xmlids(cr, xmlid_renames)
