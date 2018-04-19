import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-report-print-send",
    description="Meta package for oca-report-print-send Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-base_report_to_printer',
        'odoo9-addon-base_report_to_printer_mail',
        'odoo9-addon-printer_tray',
        'odoo9-addon-printer_zpl2',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
