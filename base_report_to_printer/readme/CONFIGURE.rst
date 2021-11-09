To configure this module, you need to:

#. Enable the "Printing / Print User" option under access
   rights to give users the ability to view the print menu.


The jobs will be sent to the printer with a name matching the print_report_name
of the report (truncated at 80 characters). By default this will not be
displayed by CUPS web interface or in Odoo. To see this information, you need
to change the configuration of your CUPS server and set the JobPrivateValue
directive to "job-name", and reload the server. See `cupsd.conf(5)
<https://www.cups.org/doc/man-cupsd.conf.html>` for details.
