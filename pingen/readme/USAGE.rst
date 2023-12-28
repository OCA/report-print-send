On the attachment view, a new pingen.com section has been added.
You can tick a box to push the document to pingen.com.

There is 3 additional options:

 * Send: the document will not be only uploaded, but will be also be sent
 * Speed: priority or economy
 * Type of print: color or black and white

Once the configuration is done and the attachment saved, a Pingen Document
is created. You can directly access to the latter on the Link on the right on
the attachment view.

You can find them in `Pingen Documents` App or in the more convenient `Documents` menu if you have installed the
`document` module.

Errors
======

Sometimes, pingen.com will refuse to send a document because it does not meet
its requirements. In such case, the document's state becomes "Pingen Error"
and you will need to manually handle the case, either from the pingen.com
backend, or by changing the document on Odoo and resolving the error on the
Pingen Document.

When a connection error occurs, the action will be retried on the next
scheduler run.


Dependencies
============

 * Require the Python library `requests_oauthlib <https://github.com/requests/requests-oauthlib>`_
 * The address must be in a format accepted by pingen.com: the last line
   is the country in English or German.
