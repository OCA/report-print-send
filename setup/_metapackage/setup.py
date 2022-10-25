import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-report-print-send",
    description="Meta package for oca-report-print-send Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-base_report_to_printer>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
