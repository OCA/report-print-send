# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
import re
from hashlib import md5

from escpos.printer import Dummy  # pylint: disable=W7936
from lxml import etree
from PIL import Image

elem_styles = {
    "h1": {"bold": "on", "size": "double"},
    "h2": {"size": "double"},
    "h3": {"bold": "on", "size": "double-height"},
    "h4": {"size": "double-height"},
    "h5": {"bold": "on"},
    "em": {"font": "b"},
    "b": {"bold": "on"},
}


def strclean(string):
    if not string:
        string = ""
    string = string.strip()
    string = re.sub(r"\s+", " ", string)
    return string


class PrinterLine:
    def __init__(self, indent=0, tabwidth=2, width=48, ratio=0.5):
        self.tabwidth = tabwidth
        self.indent = indent
        self.width = max(0, width - int(tabwidth * indent))
        self.lwidth = int(self.width * ratio)
        self.rwidth = max(0, self.width - self.lwidth)
        self.clwidth = 0
        self.crwidth = 0
        self.lbuffer = ""
        self.rbuffer = ""
        self.left = True

    def _txt(self, txt):
        if self.left:
            if self.clwidth < self.lwidth:
                txt = txt[: max(0, self.lwidth - self.clwidth)]
                self.lbuffer += txt
                self.clwidth += len(txt)
        else:
            if self.crwidth < self.rwidth:
                txt = txt[: max(0, self.rwidth - self.crwidth)]
                self.rbuffer += txt
                self.crwidth += len(txt)

    def start_inline(self, stylestack=None):
        if (self.left and self.clwidth) or (not self.left and self.crwidth):
            self._txt(" ")

    def start_block(self, stylestack=None):
        self.start_inline(stylestack)

    def end_entity(self):
        pass

    def pre(self, text):
        if text:
            self._txt(text)

    def text(self, text):
        if text:
            text = strclean(text)
            if text:
                self._txt(text)

    def linebreak(self):
        pass

    def style(self, stylestack):
        pass

    def raw(self, raw):
        pass

    def start_right(self):
        self.left = False

    def get_line(self):
        return (
            " " * self.indent * self.tabwidth
            + self.lbuffer
            + " " * (self.width - self.clwidth - self.crwidth)
            + self.rbuffer
        )


class Printer(Dummy):
    dirty = False
    img_cache = {}

    def print_xml(self, data, style=None):
        self.dirty = False
        self.stack = []
        if isinstance(data, etree._Element):
            node = data
        else:
            node = etree.fromstring(data)
        if style is None:
            style = {
                "align": "left",
                "underline": "off",
                "bold": "off",
                "size": "normal",
                "font": "a",
                "width": 48,
                "indent": 0,
                "tabwidth": 2,
                "bullet": " - ",
                "line-ratio": 0.5,
                "color": "black",
                "qrsize": 1,
            }
        self.charcode(node.attrib.get("charcode", "CP1252"))
        self._print_xml(node, style)

    def _get_style(self, node, style):
        current_style = style.copy()
        if node.tag in elem_styles:
            current_style.update(elem_styles[node.tag])
        current_style.update(node.attrib)
        return current_style

    def _set_style(
        self,
        align="left",
        font="a",
        bold=False,
        underline=0,
        width=1,
        height=1,
        density=9,
        invert=False,
        smooth=False,
        flip=False,
        double_width=False,
        double_height=False,
        size=None,
        custom_size=False,
        **kwargs
    ):
        if size == "double":
            double_height = True
            double_width = True
        elif size == "double-height":
            double_height = True
            double_width = False
        elif size == "double-width":
            double_height = False
            double_width = True
        elif size == "normal":
            double_height = False
            double_width = False
        if bold in [1, "1", True, "on"]:
            bold = True
        else:
            bold = False
        if underline in [1, "1", True, "on"]:
            underline = True
        else:
            underline = False
        if invert in [1, "1", True, "on"]:
            invert = True
        else:
            invert = False
        if smooth in [1, "1", True, "on"]:
            smooth = True
        else:
            smooth = False
        if flip in [1, "1", True, "on"]:
            flip = True
        else:
            flip = False
        if double_width in [1, "1", True, "on"]:
            double_width = True
        else:
            double_width = False
        if double_height in [1, "1", True, "on"]:
            double_height = True
        else:
            double_height = False
        if custom_size in [1, "1", True, "on"]:
            custom_size = True
        else:
            custom_size = False
        self.set(
            align=align,
            font=font,
            bold=bold,
            underline=underline,
            width=int(width),
            height=int(height),
            density=int(density),
            invert=invert,
            smooth=smooth,
            flip=flip,
            double_width=double_width,
            custom_size=custom_size,
            double_height=double_height,
        )

    def _start_block(self, style):
        if self.dirty:
            self.ln()
            self.dirty = False
        self._set_style(**style)
        self.stack.append("block")

    def text(self, text, noclean=False, *args, **kwargs):
        """
        Puts text in the entity.
        Whitespace and newlines are stripped to single spaces.
        """
        if not noclean:
            text = strclean(text)
        if text:
            self.dirty = True
            super().text(text, *args, **kwargs)

    def textln(self, text, *args, **kwargs):
        result = super().textln(text, *args, **kwargs)
        self.dirty = False
        return result

    def ln(self, *args, **kwargs):
        self.dirty = False
        return super().ln(*args, **kwargs)

    def _start_inline(self, style):
        if self.dirty:
            self.text(" ")
        self._set_style(**style)
        self.stack.append("inline")

    def _end_entity(self):
        if self.stack[-1] == "block":
            self._raw(b"\n")
        if len(self.stack) >= 1:
            self.stack = self.stack[:-1]

    def _print_xml(self, node, style, indent=0):
        current_style = self._get_style(node, style)
        if node.tag in (
            "p",
            "div",
            "section",
            "article",
            "receipt",
            "header",
            "footer",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
        ):
            self._start_block(current_style)
            if node.text:
                self.text(node.text)
            for child in node:
                self._print_xml(child, current_style, indent)
                if child.tail:
                    self._start_inline(current_style)
                    self.text(child.tail)
                    self._end_entity()
            self._end_entity()
        elif node.tag in ("span", "em", "b", "left", "right"):
            self._start_inline(current_style)
            if node.text:
                self.text(node.text)
            for child in node:
                self._print_xml(child, current_style, indent)
                self._start_inline(current_style)
                self.text(child.tail)
                self._end_entity()
            self._end_entity()
        elif hasattr(self, "_print_xml_%s" % node.tag):
            getattr(self, "_print_xml_%s" % node.tag)(
                node, current_style, style, indent=indent
            )

    def _print_xml_line(self, node, current_style, style, indent=0):
        width = int(current_style.get("width"))
        if current_style.get("size") in ("double", "double-width"):
            width = width / 2
        line_style = current_style.copy()
        line_style["width"] = width
        lineserializer = PrinterLine(
            int(current_style.get("indent")) + indent,
            int(current_style.get("tabwidth")),
            width,
            float(current_style.get("line-ratio")),
        )
        self._start_block(current_style)
        for child in node:
            if child.tag == "left":
                lineserializer.text(child.text)
            elif child.tag == "right":
                line_style["align"] = "right"
                lineserializer.start_right()
                lineserializer.text(child.text)
        self.text(lineserializer.get_line(), noclean=True)
        self.dirty = True
        self._end_entity()

    def _print_xml_ul(self, node, current_style, style, indent=0):
        self._start_block(current_style)
        bullet = current_style.get("bullet")
        for child in node:
            if child.tag == "li":
                self._set_style(current_style)
                self.raw(" " * indent * int(current_style.get("tabwidth")) + bullet)
            self._print_xml(child, current_style, indent + 1)
        self._end_entity()

    def _print_xml_ol(self, node, current_style, style, indent=0):
        cwidth = len(str(len(node))) + 2
        i = 1
        self._start_block(current_style)
        for child in node:
            if child.tag == "li":
                self._set_style(current_style)
                self.raw(
                    " " * indent * int(current_style.get("tabwidth"))
                    + " "
                    + (str(i) + ")").ljust(cwidth)
                )
                i += 1
            self._print_xml(child, current_style, indent + 1)
        self._end_entity()

    def _print_xml_pre(self, node, current_style, style, indent=0):
        self._start_block(current_style)
        self.text(node.text, noclean=True)
        self.dirty = True
        self._end_entity()

    def _print_xml_hr(self, node, current_style, style, indent=0):
        width = int(current_style.get("width"))
        if current_style.get("size") in ("double", "double-width"):
            width = width / 2
        self._start_block(current_style)
        self.text("-" * width)
        self._end_entity()

    def _print_xml_br(self, node, current_style, style, indent=0):
        self.linebreak()

    def _print_xml_qr(self, node, current_style, style, indent=0):
        self._start_block(current_style)
        self.qr(node.text, native=True, size=int(node.attrib.get("qrsize", 3)))
        self._end_entity()

    def _print_xml_img(self, node, current_style, style, indent=0):
        if "src" in node.attrib and "data:" in node.attrib["src"]:
            self.print_base64_image(node.attrib["src"])

    def _print_xml_barcode(self, node, current_style, style, indent=0):
        if "encoding" in node.attrib:
            self._start_block(current_style)
            self.barcode(strclean(node.text), node.attrib["encoding"].upper())
            self._end_entity()

    def _print_xml_partialcut(self, node, current_style, style, indent=0):
        self.cut("PART")

    def _print_xml_cut(self, node, current_style, style, indent=0):
        self.cut()

    def _print_xml_cashdraw(self, node, current_style, style, indent=0):
        self.cashdraw(2)
        self.cashdraw(5)

    def print_base64_image(self, img):
        image_id = md5.new(img).digest()
        if image_id not in self.img_cache:
            img = img[img.find(",") + 1 :]
            f = io.BytesIO("img")
            f.write(base64.decodestring(img))
            f.seek(0)
            img_rgba = Image.open(f)
            img = Image.new("RGB", img_rgba.size, (255, 255, 255))
            channels = img_rgba.split()
            if len(channels) > 1:
                img.paste(img_rgba, mask=channels[3])
            else:
                img.paste(img_rgba)
            self.img_cache[id] = img
        self.image(self.img_cache[image_id])
