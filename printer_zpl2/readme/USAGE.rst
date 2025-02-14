To print a label, you need to call use the label printing method from anywhere (other modules, server actions, etc.).

Example : Print the label of a product ::

    self.env['printing.label.zpl2'].browse(label_id).print_label(
        self.env['printing.printer'].browse(printer_id),
        self.env['product.product'].browse(product_id))

For GS1-128 barcodes:

1. Create a new label component
2. Set the component type to "GS1-128"
3. Add Application Identifiers with their configurations:
   * Select the AI type (e.g., GTIN, Weight, Date)
   * Set the field path to get the data from
   * For weight fields, optionally set the UoM field path
   * Set the sequence to control AI order
   * For weight fields, set the decimal places

The module will automatically:
* Format the data according to GS1 specifications
* Convert units of measure for weights
* Combine multiple AIs with proper separators
* Generate the final GS1-128 barcode

You can also use the generic label printing wizard, if added on some models.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/144/12.0
