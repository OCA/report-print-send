import {expect, test} from "@odoo/hoot";

import {isSupportedReportType} from "@base_report_to_printer/static/src/js/qweb_action_manager.esm";

test("Print actions route PDF engines and text reports to printer backends", () => {
    expect(isSupportedReportType("qweb-pdf")).toBe(true);
    expect(isSupportedReportType("qweb-pdf-pdfium")).toBe(true);
    expect(isSupportedReportType("qweb-pdf-wkhtmltopdf")).toBe(true);
    expect(isSupportedReportType("qweb-text")).toBe(true);
    expect(isSupportedReportType("qweb-html")).toBe(false);
});
