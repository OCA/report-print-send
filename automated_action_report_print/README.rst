.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================
Automated Action Print
======================

This module allows users to create automated actions that print a report.

It adds an optional behaviour to automated actions, and allows specifying the printer and tray.

* `Use Automated Action Printer` will use the printers defined on the automatic action.
* `Use Rules defined on Report` will use the report and user based rules defined on the report and user.

It supports triggers on all automated actions with the exception of delete (as no record exists to print)

All automated action print jobs use queue_job module from OCA to print asynchronously.

Installation
============

base_report_to_printer and queue_job are required to be installed.  Please see their README's for specific instructions.

Configuration
=============



Usage
=====

Caveat
------

The notification when a report is sent to a printer will not be
displayed for the deprecated report types (RML, Webkit, ...).

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/144/11.0


Known issues / Roadmap
======================

  * Develop an Odoo widget - similar to domain widget for setting print options


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/report-print-send/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Graeme Gellatly <g@o4sb.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
