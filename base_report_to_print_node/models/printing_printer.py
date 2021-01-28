##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
import base64
import json
import logging
import os
import time
import urllib.request
from tempfile import mkstemp
from urllib.error import HTTPError

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError

PRINTNODE_URL = "https://api.printnode.com"
TIMEOUT = 20
_logger = logging.getLogger(__name__)


class PrintingPrinter(models.Model):

    _inherit = "printing.printer"

    print_node_printer = fields.Boolean(string="Print Node Printer?")
    server_id = fields.Many2one(required=False)

    @api.model
    def _get_print_node_printer(self, print_nodeId):
        return self.env["printing.printer"].search(
            [("print_node_printer", "=", True), ("uri", "=", print_nodeId)], limit=1
        )

    @api.model
    def _print_node_status_map(self, state):
        return {"online": "available"}.get(state, "unknown")

    @api.model
    def update_print_node_printers(self):
        _logger.info("Updating Print Node Printers")
        pn_printers = self._get_response("printers")
        for pn_printer in pn_printers:
            printer = self._get_print_node_printer(pn_printer.get("id"))
            if not printer:
                printer.create(
                    {
                        "name": pn_printer["description"],
                        "system_name": pn_printer["name"],
                        "model": pn_printer["name"],
                        "location": pn_printer.get("computer", {}).get("name"),
                        "uri": pn_printer["id"],
                        "print_node_printer": True,
                        "status": self._print_node_status_map(pn_printer["state"]),
                        "status_message": pn_printer.get("state", False),
                    }
                )
        return True

    @api.model
    def update_print_node_printers_status(self):
        _logger.info("Updating Print Node Printers Status")
        pn_printers = self._get_response("printers")
        for pn_printer in pn_printers:
            printer = self._get_print_node_printer(pn_printer.get("id"))
            if printer:
                vals = {
                    "status": self._print_node_status_map(pn_printer["state"]),
                    "status_message": pn_printer.get("state", False),
                }
                printer.write(vals)

    def print_document(self, report, content, **print_opts):
        """ Print a file
        Format could be pdf, qweb-pdf, raw, ...
        """
        if len(self) != 1:
            _logger.error(
                "Print Node print called with %s but singleton is expeted."
                "Check printers configuration." % self
            )
            return super().print_document(report, content, **print_opts)

        if not self.print_node_printer:
            return super().print_document(report, content, **print_opts)

        fd, file_name = mkstemp()
        try:
            os.write(fd, content)
        finally:
            os.close(fd)

        options = self.print_options(report, **print_opts)

        _logger.debug("Sending job to PrintNode printer %s" % (self.system_name))

        try:
            res = self._submit_job(
                self.uri, options.get("format", "pdf"), file_name, options,
            )
            _logger.info("Printing job '{}' for document {}".format(res, file_name))
        except Exception as e:
            _logger.error(
                "Could not submit job to print node. This is what we get:\n%s" % e
            )
        return True

    def enable(self):
        print_node_printers = self.filtered("print_node_printer")
        print_node_printers.update_print_node_printers_status()
        return super(PrintingPrinter, self - print_node_printers).enable()

    def disable(self):
        print_node_printers = self.filtered("print_node_printer")
        print_node_printers.write(
            {"status": "unavailable", "status_message": "disabled by user"}
        )
        return super(PrintingPrinter, self - print_node_printers).disable()

    # API interaction

    @api.model
    def ReadFile(self, pathname):
        """Read contents of a file and return content.
           Args:
             pathname: string, (path)name of file.
           Returns:
           string: contents of file.
        """
        try:
            f = open(pathname, "rb")
            try:
                s = f.read()
            except IOError as error:
                _logger.info("Error reading %s\n%s", pathname, error)
            finally:
                f.close()
                return s
        except IOError as error:
            _logger.error("Error opening %s\n%s", pathname, error)
            return None

    @api.model
    def _submit_job(self, printerid, jobtype, jobsrc, options):
        """Submit a job to printerid with content of dataUrl.

        Args:
            printerid: string, the printer id to submit the job to.
            jobtype: string, must match the dictionary keys in content and
                content_type.
            jobsrc: string, points to source for job. Could be a pathname or
                id string.
        Returns:
            boolean: True = submitted, False = errors.
        """
        if jobtype in ["qweb-pdf", "pdf", "aeroo"]:
            jobtype = "pdf"
        else:
            raise UserError(_("Jobtype %s not implemented for Print Node") % (jobtype))

        content = self.ReadFile(jobsrc)
        content = base64.b64encode(content).decode("utf-8")

        # Make the title unique for each job, since the printer by default will
        # name the print job file the same as the title.
        datehour = time.strftime("%b%d%H%M", time.localtime())
        title = "{}{}".format(datehour, jobsrc)

        data = {
            "printerId": printerid,
            "title": title,
            "contentType": "pdf_base64",
            "content": content,
            "source": "created by odoo db: %s" % self.env.cr.dbname,
        }
        return self._get_response("printjobs", data)

    @api.model
    def _get_response(self, service, data=None):
        api_key = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("base_report_to_print_node.api_key")
        )
        if not api_key:
            dummy, action_id = self.env["ir.model.data"].get_object_reference(
                "base_setup", "action_general_configuration"
            )
            msg = _("You haven't configured your 'Print Node Api Key'.")
            raise RedirectWarning(msg, action_id, _("Go to the configuration panel"))
        request_url = "{}/{}".format(PRINTNODE_URL, service)
        headers = {
            "authorization": "Basic "
            + base64.b64encode(api_key.encode("UTF-8")).decode("UTF-8"),
        }
        if data:
            headers["Content-Type"] = "application/json"
        data_json = data and json.dumps(data).encode("utf-8") or None
        try:
            req = urllib.request.Request(request_url, data_json, headers)
            response = urllib.request.urlopen(req, timeout=TIMEOUT).read()
        except HTTPError:
            raise UserError(
                _("Could not connect to print node. Check your configuration")
            )
        return json.loads(response.decode("utf-8"))
