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

{'name' : 'pingen.com integration',
 'version' : '1.0',
 'author' : 'Camptocamp',
 'maintainer': 'Camptocamp',
 'license': 'AGPL-3',
 'category': 'category',
 'complexity': 'easy',
 'depends' : [],
 'description': """
Integration with pingen.com
===========================

What is pingen.com
------------------

Pingen.com is a paid online service.
It send uploaded documents by letter post.

Scope of the integration
------------------------

One can decide, per document / attachment, if it should be pushed
to pingen.com. The documents are pushed asynchronously.

Dependencies
------------

 * Require the Python library `requests <http://docs.python-requests.org/>`_
 * The PDF files sent to pingen.com have to respect some `formatting rules
   <https://stage-app.pingen.com/resources/pingen_requirements_v1_en.pdf>`_.
 * The address must be in a format accepted by pingen.com: the last line
   is the country.

""",
 'website': 'http://www.camptocamp.com',
 'init_xml': [],
 'update_xml': [
     'ir_attachment_view.xml',
     'pingen_document_view.xml',
     ],
 'demo_xml': [],
 'tests': [],
 'installable': True,
 'auto_install': False,
}
