.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================
Report To Printer
=================

This module allows users to send reports to a printer attached to the server.

It adds an optional behaviour on reports to send it directly to a printer.

* `Send to Client` is the default behaviour providing you a downloadable PDF
* `Send to Printer` prints the report on selected printer

It detects trays on printers installation plus permits to select the
paper source on which you want to print directly.

Report behaviour is defined by settings.

You will find this option on default user config, on default report
config and on specific config per user per report.

This allows you to dedicate a specific paper source for example for
preprinted paper such as payment slip.

Settings can be configured:

* globally
* per user
* per report
* per user and report

Installation
============

* Install PyCups - https://pypi.python.org/pypi/pycups

.. code-block:: bash

   sudo apt-get install cups
   sudo apt-get install libcups2-dev
   sudo apt-get install python3-dev
   sudo pip install pycups


Configuration
=============

After installing enable the "Printing / Print User" option under access
rights to give users the ability to view the print menu.


Usage
=====

 * To update the CUPS printers in *Settings > Printing > Update Printers
   from CUPS*
 * If you want to print a report on a specific printer or tray, you can change
   these in *Settings > Printing > Reports* to define default behaviour.
 * If you want to print a report on a specific printer and/or tray for a user, you can
   change these in *Settings > Printing > Reports* in
   *Specific actions per user*
 * Users may also select a default action, printer or tray in their preferences

When no tray is configured for a report and a user, the
default tray setup on the CUPS server is used.

Caveat
------

The notification when a report is sent to a printer will not be
displayed for the deprecated report types (RML, Webkit, ...).

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/144/11.0


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

* Ferran Pegueroles <ferran@pegueroles.com>
* Albert Cervera i Areny <albert@nan-tic.com>
* Davide Corio <davide.corio@agilebg.com>
* Lorenzo Battistini <lorenzo.battistini@agilebg.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Lionel Sausin <ls@numerigraphe.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Dave Lasley <dave@laslabs.com>
* Sylvain Garancher <sylvain.garancher@syleam.fr>
* Jairo Llopis <jairo.llopis@tecnativa.com>

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
