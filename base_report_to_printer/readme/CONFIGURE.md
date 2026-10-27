Configuration Guide

To configure and start using the Base Report to Printer module, follow these steps:

1. User Access Rights

Go to Settings → Users & Companies → Users.

Open the user form and in the Access Rights tab, enable:

Printing / Print User → grants access to the printing menu and user-specific printing preferences.

2. Global Printing Settings

Navigate to Settings → Technical → Printing → Printing Settings.

Define the default printing behavior for reports:

Send to Client (default): generates a downloadable PDF.

Send to Printer: sends the report directly to a configured printer (requires a backend module such as base_report_to_printer_cups).

3. User Preferences

Each user can configure their own printing behavior:

Go to Preferences (top-right menu, click on your name).

In the Printing section, choose:

Default action (Send to Client / Send to Printer).

Preferred printer (if a backend module is installed and printers are detected).

4. Report-Specific Configuration

Go to Settings → Technical → Reports → Reports.

For each report, you can define:

Default printing action.

Default printer (if available).

These settings can be overridden at the user level.

5. Per User & Report Combination

Navigate to Settings → Technical → Printing → Report Configurations.

Here you can assign specific rules combining:

A user.

A report.

A printing action (Send to Client / Send to Printer).

A printer and tray (if supported by the backend).

6. Installing a Backend (e.g., CUPS)

The base module does not include any printing backend. To connect with actual printers you must install an extension module, such as:

base_report_to_printer_cups → adds support for CUPS printers, trays, and job management.

Once installed, printers from the backend will be available in the configuration menus above.
