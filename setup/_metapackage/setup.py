import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-report-print-send",
    description="Meta package for oca-report-print-send Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-base_report_to_printer',
        'odoo10-addon-printer_tray',
        'odoo10-addon-printer_zpl2',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
