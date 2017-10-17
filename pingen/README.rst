.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===========================
Integration with pingen.com
===========================

What is pingen.com
==================

Pingen.com is a paid online service.
It sends uploaded documents by letter post.

Scope of the integration
========================

One can decide, per document / attachment, if it should be pushed
to pingen.com. The documents are pushed asynchronously.

A second cron updates the informations of the documents from pingen.com, so we
know which of them have been sent.

Configuration
=============

The authentication token is configured on the company's view. You can also
tick a checkbox if the staging environment (https://stage-api.pingen.com)
should be used.

The setup of the 2 crons can be changed as well:

 * Run Pingen Document Push
 * Run Pingen Document Update

Usage
=====

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
======

Sometimes, pingen.com will refuse to send a document because it does not meet
its requirements. In such case, the document's state becomes "Pingen Error"
and you will need to manually handle the case, either from the pingen.com
backend, or by changing the document on OpenERP and resolving the error on the
Pingen Document.

When a connection error occurs, the action will be retried on the next
scheduler run.

Dependencies
============

 * Require the Python library `requests <http://docs.python-requests.org/>`_
 * The PDF files sent to pingen.com have to respect some `formatting rules
   <https://stage-app.pingen.com/resources/pingen_requirements_v1_en.pdf>`_.
 * The address must be in a format accepted by pingen.com: the last line
   is the country in English or German.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/report-print-send/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
============

* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Anar Baghirli <a.baghirli@mobilunity.com>

Maintainer
==========

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
