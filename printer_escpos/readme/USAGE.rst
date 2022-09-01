To print a ticket, you need to call the ticket printing method.
It can be used anywhere (other modules, server actions, etc.).

Example : Print a ticket of a product ::

    self.env['printing.escpos'].browse(ticket_id).print_escpos(
        self.env['printing.printer'].browse(printer_id),
        self.env['product.product'].browse(product_id))

You can also use the generic ticket printing wizard, if added on some models.

Format of the ticket
~~~~~~~~~~~~~~~~~~~~

The ESCPOS expects an XML with root tag receipt.
Inside we can use the following tags:

*  p
*  div
*  section
*  article
*  receipt
*  header
*  footer
*  li
*  h1
*  h2
*  h3
*  h4
*  h5
*  line: Allows to manage lines. Each column must be right or left
*  ul: Bullet list
*  ol: Ordered list
*  pre
*  hr
*  br: Line break
*  qr: Inserts a QR. The text will be the value of the QR. With attribute qrsize we can make it bigger
*  img: Inserts an image
*  barcode: Inserts a barcode. Expects an attribute encoding in order to know which kind of barcode
*  cut
*  partialcut
*  cashdraw: Opens the cashdraw if configured

At any tag we can add the following attributes in order to modify the style:

*  align
*  underline: Can be on or off
*  bold: Can be on or off
*  size: Can be normal, double, double-height or double-weight
*  font: Can be A or B
*  width
*  indent
*  tabwidth
*  bullet: Describes the bullet description. By default ` - `
*  line-ratio
*  color
