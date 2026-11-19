On the attachment view, a new pingen.com section has been added. You can
tick a box to push the document to pingen.com.

There is 3 additional options:

> - Send: the document will not be only uploaded, but will be also be
>   sent
> - Speed: priority or economy
> - Type of print: color or black and white

Once the configuration is done and the attachment saved, a Pingen
Document is created. You can directly access to the latter on the Link
on the right on the attachment view.

You can find them in Pingen Documents App or in the more convenient
Documents menu if you have installed the document module.

Deleting a Pingen document also deletes its attachment unless it is linked to
another record.

## Errors

Sometimes, pingen.com will refuse to send a document because it does not
meet its requirements. In such case, the document's state becomes
"Pingen Error" and you will need to manually handle the case, either
from the pingen.com backend, or by changing the document on Odoo and
resolving the error on the Pingen Document.

When a connection error occurs, the action will be retried on the next
scheduler run.

## Dependencies

> - Require the Python library
>   [requests_oauthlib](https://github.com/requests/requests-oauthlib)
> - The address must be in a format accepted by pingen.com: the last
>   line is the country in English or German.

## Layout check

Before uploading to Pingen, every PDF page is checked for content within 5 mm
of any edge and in the lower-left 15 mm × 15 mm square. Detected content blocks
the upload and sets the document to "Pingen Error". Correct the layout and
create a new document. The postage area and address window are not checked.
If the PDF cannot be inspected, the upload proceeds for Pingen to validate it.

## Letter information before sending

After upload, the document shows the address read by Pingen, destination country,
page count and estimated cost in the indicated currency. The estimate uses the
selected delivery and printing options; refresh the letter information after
changing them. Uploaded letters that have not been sent yet are refreshed every
hour. The actual cost appears after sending.

A document uploaded with Send disabled is still sent by the scheduled action
*Run Pingen Document Push* (hourly) unless that action is disabled. Use the
*Ask pingen.com to send the document* button to send it earlier.
