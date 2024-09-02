import json

from werkzeug.urls import url_parse

from odoo import http
from odoo.http import content_disposition, request
from odoo.tools.misc import html_escape
from odoo.tools.safe_eval import safe_eval, time

from odoo.addons.web.controllers.report import ReportController

DEFAULT_RESOLUTION = "200"


class ReportController(ReportController):
    """Changing report controller to have zpl reports export as .zpl
    (and later on be processed to directly print to a zebra printer)
    """

    @http.route(["/report/download"], type="http", auth="user", cors="*")
    def report_download(self, data, context=None, token=None):
        """This function is used by 'zplactionmanager.js' in order to trigger
        the download of a zpl report.

        :param data: a javascript array JSON.stringified containg report
        internal url ([0]) and type [1]
        :returns: Response with a filetoken cookie and an attachment header
        """
        requestcontent = json.loads(data)
        url, report_type = requestcontent[0], requestcontent[1]
        if "zpl" not in report_type:
            return super().report_download(data, context=context, token=token)
        try:
            resolution = (
                requestcontent[2] if len(requestcontent) == 3 else DEFAULT_RESOLUTION
            )
            reportname = url.split("/report/zpl/")[1].split("?")[0]
            docids = None
            if "/" in reportname:
                reportname, docids = reportname.split("/")

            if docids:
                # Generic report:
                response = self.report_routes(
                    reportname,
                    docids=docids,
                    context=json.dumps({"resolution": resolution}),
                    converter="text",
                )
            else:
                # Particular report:
                # decoding the args represented in JSON
                data = url_parse(url).decode_query(cls=dict)
                if "context" in data:
                    context, data_context = json.loads(context or "{}"), json.loads(
                        data.pop("context")
                    )
                    context = json.dumps(
                        {**context, **data_context, "resolution": resolution}
                    )
                response = self.report_routes(
                    reportname, converter="text", context=context, **data
                )

            report = request.env["ir.actions.report"]._get_report_from_name(reportname)
            filename = "%s.zpl" % (report.name)

            if docids:
                ids = [int(x) for x in docids.split(",") if x.isdigit()]
                obj = request.env[report.model].browse(ids)
                if report.print_report_name and not len(obj) > 1:
                    report_name = safe_eval(
                        report.print_report_name, {"object": obj, "time": time}
                    )
                    filename = "%s.zpl" % (report_name)
            response.headers.add("Content-Disposition", content_disposition(filename))
            return response
        except Exception as e:
            se = http.serialize_exception(e)
            error = {"code": 200, "message": "Odoo Server Error", "data": se}
            return request.make_response(html_escape(json.dumps(error)))
