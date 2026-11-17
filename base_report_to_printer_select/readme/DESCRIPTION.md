This module lets the user choose the printer at print time. It adds the
**Ask the user** behaviour to the printing actions of
**base_report_to_printer**: when a report configured that way is printed,
a dialog lists the printers that can handle it and one click sends the
job to the selected one. Printers declare the paper formats they support,
so only the printers matching the paper format of the report are offered,
and the last printer picked by each user for each report is proposed
first.
