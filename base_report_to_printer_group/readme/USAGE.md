When a user prints a report, the printing behaviour is resolved in this
order:

1.  The specific action of the user for the report.
2.  The specific action of the first of the user's groups, by sequence,
    that has a line for the report.
3.  The default behaviour and printer of the report.
4.  The defaults of the user.

When the report asks the user to select a printer, the dialog proposes
the printers of the user's groups that support the paper format of the
report. **See more** reveals the other printers of that paper format,
outside the user's groups; printers of another paper format are never
offered.
