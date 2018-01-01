.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

========================================
Report to printer - Paper tray selection
========================================

Extends the module **Report to printer** (``base_report_to_printer``)
to add the printers trays.

It detects trays on printers installation plus permits to select the
paper source on which you want to print directly.

You will find this option on default user config, on default report
config and on specific config per user per report.

This allows you to dedicate a specific paper source for example for
preprinted paper such as payment slip.

Installation
============

Considering that you already use the module **Report to printer**, you
just have to install this extension.

Configuration
=============

To configure this module, you need to:

 * Update the CUPS printers in *Settings > Printing > Update Printers
   from CUPS*
 * If you want to print a report on a specific tray, you can change
   their "Paper Source" in *Settings > Printing > Reports*
 * If you want to print a report on a specific tray for a user, you can
   change their "Paper Source" in *Settings > Printing > Reports* in
   *Specific actions per user*
 * Users may also select a default tray in their preferences

Usage
=====

There is no special usage, once configured, reports are printed in the
select tray. When no tray is configured for a report and a user, the
default tray setup on the CUPS server is used.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/144/10.0

Known issues / Roadmap
======================



Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/report-print-send/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>

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
