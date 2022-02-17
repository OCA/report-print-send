import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-report-print-send",
    description="Meta package for oca-report-print-send Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-base_report_to_printer',
        'odoo14-addon-base_report_to_printer_mail',
        'odoo14-addon-printer_zpl2',
        'odoo14-addon-remote_report_to_printer',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
