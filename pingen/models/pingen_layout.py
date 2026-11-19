# Copyright 2026 Altixia LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def find_restricted_content(
    pdf_bytes, border_mm=5.0, corner_mm=15.0, dpi=100, white_threshold=240
) -> list[tuple[int, str]]:
    """Find ink in each page's edge bands and lower-left square.

    Floor the band sizes to avoid reporting pixels exactly at the limit.
    Zones are independent: the corner can overlap the left and bottom bands.
    A failed inspection always leaves the final decision to Pingen.
    """
    try:
        import pymupdf

        border = int(border_mm * dpi / 25.4)
        corner = int(corner_mm * dpi / 25.4)
        violations = []
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
            if (
                not document.is_pdf
                or document.is_encrypted
                or document.metadata.get("encryption")
            ):
                raise ValueError("Not a readable, unencrypted PDF")
            for number, page in enumerate(document, start=1):
                pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
                samples = pixmap.samples
                width, height, stride = pixmap.width, pixmap.height, pixmap.stride
                bx, by = min(border, width), min(border, height)
                cx, cy = min(corner, width), min(corner, height)
                zones = (
                    ("top", 0, 0, width, by),
                    ("bottom", 0, height - by, width, height),
                    ("left", 0, 0, bx, height),
                    ("right", width - bx, 0, width, height),
                    ("bottom_left_corner", 0, height - cy, cx, height),
                )
                for zone, x0, y0, x1, y1 in zones:
                    if any(
                        min(samples[y * stride + x0 : y * stride + x1], default=255)
                        < white_threshold
                        for y in range(y0, y1)
                    ):
                        violations.append((number, zone))
        return violations
    except Exception as error:  # noqa: BLE001 - inspection must fail open
        _logger.warning("Unable to inspect Pingen PDF layout: %s", error)
        return []
