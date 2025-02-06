import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-report-print-send",
    description="Meta package for oca-report-print-send Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-base_report_to_label_printer>=16.0dev,<16.1dev',
        'odoo-addon-base_report_to_printer>=16.0dev,<16.1dev',
        'odoo-addon-base_report_to_printer_mail>=16.0dev,<16.1dev',
        'odoo-addon-pingen>=16.0dev,<16.1dev',
        'odoo-addon-pingen_env>=16.0dev,<16.1dev',
        'odoo-addon-printer_zpl2>=16.0dev,<16.1dev',
        'odoo-addon-printing_simple_configuration>=16.0dev,<16.1dev',
        'odoo-addon-remote_report_to_printer>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
