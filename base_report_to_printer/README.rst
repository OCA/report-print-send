Report to printer
-----------------
This module allows users to send reports to a printer attached to the server.


It adds an optional behaviour on reports to send it directly to a printer.

* `Send to Client` is the default behavious providing you a downloadable PDF
* `Send to Printer` prints the report on selected printer

Report behaviour is defined by settings.


Settings can be configured:

* globaly
* per user
* per report
* per user and report


After installing enable the "Printing / Print Operator" option under access
rights to give users the ability to view the print menu.


To show all available printers for your server, uses
`Settings/Configuration/Printing/Update Printers from CUPS` wizard.


Then goto the user profile and set the users printing action and default
printer.


Dependencies
------------

This module requires pycups
https://pypi.python.org/pypi/pycups


Contributors
------------

* Ferran Pegueroles <ferran@pegueroles.com>
* Albert Cervera i Areny <albert@nan-tic.com>
* Davide Corio <davide.corio@agilebg.com>
* Lorenzo Battistini <lorenzo.battistini@agilebg.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Lionel Sausin <ls@numerigraphe.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
