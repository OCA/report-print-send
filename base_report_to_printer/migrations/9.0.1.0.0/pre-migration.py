# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenUpgrade module for Odoo
#    @copyright 2014-Today: Odoo Community Association
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
