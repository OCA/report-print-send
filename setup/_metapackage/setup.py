import setuptools

with open("VERSION.txt", "r") as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-report-print-send",
    description="Meta package for oca-report-print-send Odoo addons",
    version=version,
    install_requires=["odoo13-addon-base_report_to_printer"],
    classifiers=["Programming Language :: Python", "Framework :: Odoo"],
)
