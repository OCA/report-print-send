To configure this module, you need to:

1.  Go to *Settings \> Printing \> Labels \> ZPL II*
2.  Create new labels
3.  Import ZPL2 code
4.  Use the Test Mode tab during the creation

It's also possible to add a label printing wizard on any model by
creating a new *ir.actions.act_window* record. For example, to add the
printing wizard on the *product.product* model :

    <act_window id="action_wizard_purchase"
      name="Print Label"
      src_model="product.product"
      res_model="wizard.print.record.label"
      view_mode="form"
      target="new"
      key2="client_action_multi"/>
