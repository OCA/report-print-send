To configure this module, you need to:

1.  Go to *Settings \> Technical \> Printing \> Printers* and fill in
    **Paper formats** on each printer with the formats it can print. A
    printer with no paper format accepts any report.
2.  Make sure the reports that should ask for a printer have the right
    **Paper format** on their *Advanced Properties* tab. This module shows
    the field on text reports too, so label reports (ZPL) can carry a
    dedicated paper format (for example a 4x6" one) that is also set on
    the label printers. A PDF report without a paper format uses the one
    of the company; a text report without one accepts any printer.
3.  Go to *Settings \> Technical \> Printing \> Reports*, open a report
    and set its **Default Behaviour** to a printing action of type
    **Ask the user**. The type is also available on the *Specific actions
    per user* lines and as the default printing action of a user.
