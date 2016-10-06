# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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

{
    'name': 'pingen.com integration',
    'version': '1.0',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'maintainer': 'Camptocamp',
    'license': 'AGPL-3',
    'category': 'Reporting',
    'complexity': 'easy',
    'depends': [],
    'external_dependencies': {
        'python': ['requests'],
        },
    'description': """
Integration with pingen.com
===========================

What is pingen.com
------------------

Pingen.com is a paid online service.
It sends uploaded documents by letter post.

Scope of the integration
------------------------

One can decide, per document / attachment, if it should be pushed
to pingen.com. The documents are pushed asynchronously.

A second cron updates the informations of the documents from pingen.com, so we
know which of them have been sent.

Configuration
-------------

The authentication token is configured on the company's view. You can also
tick a checkbox if the staging environment (https://stage-api.pingen.com)
should be used.

The setup of the 2 crons can be changed as well:

 * Run Pingen Document Push
 * Run Pingen Document Update

Usage
-----

On the attachment view, a new pingen.com tab has been added.
You can tick a box to push the document to pingen.com.

There is 3 additional options:

 * Send: the document will not be only uploaded, but will be also be sent
 * Speed: priority or economy
 * Type of print: color or black and white

Once the configuration is done and the attachment saved, a Pingen Document
is created. You can directly access to the latter on the Link on the right on
the attachment view.

You can find them in `Settings > Customization > Low Level Objets > Pingen
Documents` or in the more convenient `Documents` menu if you have installed the
`document` module.

Errors
------

Sometimes, pingen.com will refuse to send a document because it does not meet
its requirements. In such case, the document's state becomes "Pingen Error" and
you will need to manually handle the case, either from the pingen.com backend,
or by changing the document on OpenERP and resolving the error on the Pingen
Document.

When a connection error occurs, the action will be retried on the next scheduler
run.

Dependencies
------------

 * Require the Python library `requests <http://docs.python-requests.org/>`_
 * The PDF files sent to pingen.com have to respect some `formatting rules
   <https://stage-app.pingen.com/resources/pingen_requirements_v1_en.pdf>`_.
 * The address must be in a format accepted by pingen.com: the last line
   is the country in English or German.

""",
    'website': 'http://www.camptocamp.com',
    'data': [
        'ir_attachment_view.xml',
        'pingen_document_view.xml',
        'pingen_data.xml',
        'res_company_view.xml',
        'security/ir.model.access.csv',
        ],
    'tests': [],
    'installable': False,
    'auto_install': False,
    'application': True,
}
