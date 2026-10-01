This document explains how to configure the **base_report_to_printer_qz** module
before using it. It is intended for users with **administration privileges**.

---

## 1. Configure a Printer Using QZ Tray Backend

The module relies on printers configured in Odoo that use the **QZ Tray backend**.

### Create or Configure a Printer

1. Go to **Settings → Technical → Printing → Printers**.
2. Click **Create** (or open an existing printer).
3. Configure the printer with the following values:

   - **Name**:
     Must match **exactly** the printer name installed on the client operating system
     and visible in QZ Tray.
   - **Backend**:
     Select **QZ Tray**.

> The print jobs will be sent to the locally installed printer whose name matches
> the configured printer name in Odoo.

---

## 3. Assign the Printer (Optional but Recommended)

You can define which printer is used by default at different levels.

### Per User

1. Go to **Settings → Users & Companies → Users**.
2. Open the user.
3. Set:
   - **Printing Action** (e.g. *Send to Printer*).
   - **Printing Printer** (select the QZ Tray printer created earlier).
4. Save.

### Per Report (Optional)

1. Go to **Settings → Technical → Reports**.
2. Open the report you want to print automatically.
3. Configure:
   - **Printing Action**
   - **Printing Printer**
4. Save.

User-level settings will always take precedence over report-level settings.

---

## 4. Client-Side Requirements

Ensure the following on each client machine:

- **QZ Tray** is installed and running.
- The client trusts the certificate configured in Odoo.
- The printer is installed locally and its name matches the one configured in Odoo.

---

Once these steps are completed, reports configured to be sent to the printer
will be printed through **QZ Tray** without further user interaction.
