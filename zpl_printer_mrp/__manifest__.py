{
    "name": "ZPL Printer Management (Production related)",
    "version": "18.0.0.0.1",
    "category": "Hidden",
    "summary": "Connects ZPL-Printers with Production",
    "author": "Thomas Kosel, Voltfang GmbH," " Odoo Community Association (OCA),",
    "website": "https://github.com/OCA/report-print-send",
    "license": "AGPL-3",
    "depends": ["zpl_printer", "mrp"],
    "data": ["report/mrp_report_views_main.xml", "views/mrp_workcenter_views.xml"],
    "assets": {},
    "installable": True,
    "auto_install": True,
}
