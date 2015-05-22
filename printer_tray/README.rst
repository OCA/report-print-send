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

Known issues / Roadmap
======================



Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/report-print-send/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/report-print-send/issues/new?body=module:%20printer_tray%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
