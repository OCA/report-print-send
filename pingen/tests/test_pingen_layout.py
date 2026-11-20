# Copyright 2026 Altixia LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import sys
from unittest.mock import patch

import pymupdf

from odoo.tests.common import BaseCase

from ..models import pingen_layout as _layout
from ..models.pingen_layout import find_restricted_content

MM = 72 / 25.4


class TestPingenLayout(BaseCase):
    def make_pdf(self, rectangles=(), pages=1, marked_page=0):
        with pymupdf.open() as document:
            for index in range(pages):
                page = document.new_page(width=210 * MM, height=297 * MM)
                if index == marked_page:
                    for rectangle in rectangles:
                        page.draw_rect(
                            pymupdf.Rect(*(value * MM for value in rectangle)),
                            color=None,
                            fill=(0, 0, 0),
                        )
            return document.tobytes()

    def test_blank_a4(self):
        self.assertEqual(find_restricted_content(self.make_pdf()), [])

    def test_left_margin(self):
        pdf = self.make_pdf([(3, 100, 4, 105)])
        self.assertEqual(find_restricted_content(pdf), [(1, "left")])

    def test_right_margin(self):
        pdf = self.make_pdf([(205, 100, 206, 105)])
        self.assertEqual(find_restricted_content(pdf), [(1, "right")])

    def test_outside_right_margin(self):
        pdf = self.make_pdf([(203, 100, 204, 105)])
        self.assertEqual(find_restricted_content(pdf), [])

    def test_corner_only(self):
        # Nearest edges are 10 mm away: outside the 5 mm bands, inside the square.
        pdf = self.make_pdf([(10, 286, 11, 287)])
        self.assertEqual(find_restricted_content(pdf), [(1, "bottom_left_corner")])

    def test_corner_and_left_margin(self):
        pdf = self.make_pdf([(3, 286, 4, 287)])
        self.assertEqual(
            find_restricted_content(pdf), [(1, "left"), (1, "bottom_left_corner")]
        )

    def test_outside_corner(self):
        pdf = self.make_pdf([(20, 276, 21, 277)])
        self.assertEqual(find_restricted_content(pdf), [])

    def test_top_and_bottom(self):
        pdf = self.make_pdf([(100, 3, 105, 4), (100, 293, 105, 294)])
        self.assertEqual(find_restricted_content(pdf), [(1, "top"), (1, "bottom")])

    def test_second_page(self):
        pdf = self.make_pdf([(3, 100, 4, 105)], pages=3, marked_page=1)
        self.assertEqual(find_restricted_content(pdf), [(2, "left")])

    def test_border_limit(self):
        pdf = self.make_pdf([(5, 100, 6, 105)])
        self.assertEqual(find_restricted_content(pdf), [])

    def test_invalid_pdf(self):
        with self.assertLogs(_layout.__name__, level="WARNING"):
            self.assertEqual(find_restricted_content(b"not a PDF"), [])

    def test_encrypted_pdf(self):
        with pymupdf.open(stream=self.make_pdf(), filetype="pdf") as document:
            pdf = document.tobytes(
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                owner_pw="owner",
                user_pw="reader",
            )
        with self.assertLogs(_layout.__name__, level="WARNING"):
            self.assertEqual(find_restricted_content(pdf), [])

    def test_missing_pymupdf(self):
        with (
            patch.dict(sys.modules, {"pymupdf": None}),
            self.assertLogs(_layout.__name__, level="WARNING"),
        ):
            self.assertEqual(find_restricted_content(b"PDF"), [])

    def test_render_failure_discards_partial_result(self):
        pdf = self.make_pdf([(3, 100, 4, 105)], pages=2)
        render = pymupdf.Page.get_pixmap

        def render_page(page, **kwargs):
            if page.number == 1:
                raise RuntimeError("render failed")
            return render(page, **kwargs)

        with (
            patch.object(pymupdf.Page, "get_pixmap", render_page),
            self.assertLogs(_layout.__name__, level="WARNING"),
        ):
            self.assertEqual(find_restricted_content(pdf), [])

    def test_full_page_white_image(self):
        with pymupdf.open() as document:
            page = document.new_page(width=210 * MM, height=297 * MM)
            image = pymupdf.Pixmap(pymupdf.csGRAY, (0, 0, 210, 297), False)
            image.clear_with(255)
            page.insert_image(page.rect, pixmap=image)
            self.assertEqual(find_restricted_content(document.tobytes()), [])
