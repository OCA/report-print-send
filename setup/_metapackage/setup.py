import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-report-print-send",
    description="Meta package for oca-report-print-send Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-base_report_to_printer',
        'odoo11-addon-printer_zpl2',
        'odoo11-addon-remote_report_to_printer',
        'odoo11-addon-stock_picking_auto_print',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
