# Usage

Guidelines for use:

- To use a specific printing backend (e.g. CUPS), make sure the corresponding module
  (such as `base_report_to_printer_cups`) is installed and configured.
- To print a report on a specific printer or tray, you can configure defaults in
  *Settings > Printing > Reports*.
- To define user-specific behaviour, go to
  *Settings > Printing > Reports* and configure *Specific actions per user*.
- Each user can also select a default action, printer or tray in their *Preferences*.
- When no tray is configured for a report or a user, the default tray defined by the printing backend (e.g. the CUPS server) will be used.

## Notes

- This module (`base_report_to_printer`) only provides the **base framework**.
- To connect with a real print system, you must install an additional backend module (e.g. `base_report_to_printer_cups` for CUPS).
- Other backend modules can be developed to support different print protocols or environments.
