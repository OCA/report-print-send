import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        'external_dependencies_override': {
            'python': {
                'python-escpos': 'python-escpos @git+https://github.com/python-escpos/python-escpos.git@v3.0a8#egg=python-escpos',
            },
        },
    }
)
