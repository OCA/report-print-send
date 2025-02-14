To configure this module, you need to:

#. Go to *Settings > Printing > Labels > ZPL II*
#. Create new labels
#. Import ZPL2 code
#. Use the Test Mode tab during the creation

For GS1-128 barcodes, you can configure:

* Supported Application Identifiers (AIs):
    * (00) SSCC
    * (01) GTIN
    * (10) Batch/Lot Number
    * (11) Production Date (YYMMDD)
    * (13) Packaging Date (YYMMDD)
    * (15) Best Before Date (YYMMDD)
    * (17) Expiration Date (YYMMDD)
    * (21) Serial Number
    * (30) Count
    * (310n) Net Weight (kg)
    * (320n) Net Weight (lbs)

* For each AI:
    * Field path to get data from (e.g., "product_id.weight")
    * For weight fields, UoM field path for automatic conversion
    * Sequence order in the final barcode
    * For weight AIs, number of decimal places (0-5)

It's also possible to add a label printing wizard on any model by creating a new *ir.actions.act_window* record.
For example, to add the printing wizard on the *product.product* model ::

    <act_window id="action_wizard_purchase"
      name="Print Label"
      src_model="product.product"
      res_model="wizard.print.record.label"
      view_mode="form"
      target="new"
      key2="client_action_multi"/>
