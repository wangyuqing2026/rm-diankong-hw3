# -*- coding: utf-8 -*-
"""生成《电控组第三次作业实施手册》的排版工具层。
提供 H（Helper）对象，把内容写法简化成 h1/p/code/table 之类的调用。"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml, OxmlElement

CN_FONT = '微软雅黑'
CODE_FONT = 'Consolas'
ACCENT = RGBColor(0x1F, 0x4E, 0x79)      # 深蓝
ACCENT2 = RGBColor(0x2E, 0x74, 0xB5)
GREY = RGBColor(0x59, 0x59, 0x59)


def _set_run_font(run, name=CN_FONT, size=None, bold=None, color=None, code=False):
    font = run.font
    font.name = CODE_FONT if code else name
    if size is not None:
        font.size = Pt(size)
    if bold is not None:
        font.bold = bold
    if color is not None:
        font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), CN_FONT if not code else CODE_FONT)
    rFonts.set(qn('w:ascii'), CODE_FONT if code else name)
    rFonts.set(qn('w:hAnsi'), CODE_FONT if code else name)


def _shade(element_pr, fill):
    element_pr.append(parse_xml(
        r'<w:shd {} w:val="clear" w:color="auto" w:fill="{}"/>'.format(nsdecls('w'), fill)))


def _para_shade(paragraph, fill):
    _shade(paragraph._p.get_or_add_pPr(), fill)


def _para_border(paragraph, color='D0D7DE', size='6'):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = parse_xml(
        r'<w:pBdr {}>'
        r'<w:left w:val="single" w:sz="{}" w:space="6" w:color="{}"/>'
        r'</w:pBdr>'.format(nsdecls('w'), size, color))
    pPr.append(pBdr)


class H:
    """文档构建助手"""

    def __init__(self, doc):
        self.doc = doc
        self.h1_no = 0
        self.h2_no = 0

    # ---------- 文本 ----------
    def _rich(self, paragraph, text, size=10.5, color=None, bold=False):
        """支持 **粗体** 与 `代码` 的行内标记，且允许在粗体里嵌代码"""
        import re
        tokens = re.split(r'(\*\*.+?\*\*|`[^`]+`)', text)
        for tok in tokens:
            if not tok:
                continue
            if tok.startswith('**') and tok.endswith('**') and len(tok) > 4:
                self._rich(paragraph, tok[2:-2], size=size, color=color, bold=True)
            elif tok.startswith('`') and tok.endswith('`') and len(tok) > 2:
                run = paragraph.add_run(tok[1:-1])
                _set_run_font(run, size=size - 0.5, code=True, color=RGBColor(0xB0, 0x30, 0x60))
            else:
                run = paragraph.add_run(tok)
                _set_run_font(run, size=size, bold=bold, color=color)

    def title(self, text, sub=None, meta=None):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(90)
        p.paragraph_format.space_after = Pt(6)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        _set_run_font(run, size=26, bold=True, color=ACCENT)

        if sub:
            p2 = self.doc.add_paragraph()
            p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p2.paragraph_format.space_after = Pt(24)
            run = p2.add_run(sub)
            _set_run_font(run, size=13, color=ACCENT2)

        line = self.doc.add_paragraph()
        line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        line.paragraph_format.space_after = Pt(40)
        run = line.add_run('—' * 18)
        _set_run_font(run, size=10, color=RGBColor(0xC0, 0xC0, 0xC0))

        if meta:
            for m in meta:
                pm = self.doc.add_paragraph()
                pm.alignment = WD_ALIGN_PARAGRAPH.CENTER
                pm.paragraph_format.space_after = Pt(4)
                run = pm.add_run(m)
                _set_run_font(run, size=10.5, color=GREY)

    def banner(self, text, sub=None):
        """紧凑标题：用于短文档（不占整页）"""
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(text)
        _set_run_font(run, size=22, bold=True, color=ACCENT)
        if sub:
            p2 = self.doc.add_paragraph()
            p2.paragraph_format.space_after = Pt(10)
            run = p2.add_run(sub)
            _set_run_font(run, size=11, color=ACCENT2)
        pPr = p._p.get_or_add_pPr()
        pPr.append(parse_xml(
            r'<w:pBdr {}><w:bottom w:val="single" w:sz="12" w:space="4" w:color="1F4E79"/></w:pBdr>'
            .format(nsdecls('w'))))

    def h1(self, text, newpage=True):
        self.h1_no += 1
        self.h2_no = 0
        if newpage:
            self.doc.add_page_break()
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18 if not newpage else 0)
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run(text)
        _set_run_font(run, size=17, bold=True, color=ACCENT)
        # 下划横线
        pPr = p._p.get_or_add_pPr()
        pBdr = parse_xml(
            r'<w:pBdr {}><w:bottom w:val="single" w:sz="12" w:space="4" w:color="1F4E79"/></w:pBdr>'
            .format(nsdecls('w')))
        pPr.append(pBdr)

    def h2(self, text):
        self.h2_no += 1
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        _set_run_font(run, size=13, bold=True, color=ACCENT2)

    def h3(self, text):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        _set_run_font(run, size=11.5, bold=True, color=RGBColor(0x40, 0x40, 0x40))

    def p(self, text, size=10.5, space_after=6):
        para = self.doc.add_paragraph()
        para.paragraph_format.space_after = Pt(space_after)
        para.paragraph_format.line_spacing = 1.35
        self._rich(para, text, size=size)
        return para

    def small(self, text):
        return self.p(text, size=9.5)

    def bullet(self, text, level=0):
        para = self.doc.add_paragraph()
        para.paragraph_format.left_indent = Cm(0.75 + 0.6 * level)
        para.paragraph_format.first_line_indent = Cm(-0.4)
        para.paragraph_format.space_after = Pt(3)
        para.paragraph_format.line_spacing = 1.3
        mark = '• ' if level == 0 else '– '
        run = para.add_run(mark)
        _set_run_font(run, size=10.5, color=ACCENT2)
        self._rich(para, text)
        return para

    def num(self, n, text):
        para = self.doc.add_paragraph()
        para.paragraph_format.left_indent = Cm(0.85)
        para.paragraph_format.first_line_indent = Cm(-0.55)
        para.paragraph_format.space_after = Pt(3)
        para.paragraph_format.line_spacing = 1.3
        run = para.add_run(f'{n}. ')
        _set_run_font(run, size=10.5, bold=True, color=ACCENT2)
        self._rich(para, text)
        return para

    def code(self, text, caption=None):
        lines = text.strip('\n').split('\n')
        for i, line in enumerate(lines):
            para = self.doc.add_paragraph()
            pf = para.paragraph_format
            pf.space_before = Pt(6 if i == 0 else 0)
            pf.space_after = Pt(6 if i == len(lines) - 1 else 0)
            pf.line_spacing = 1.12
            pf.left_indent = Cm(0.2)
            pf.keep_with_next = (i < len(lines) - 1)
            _para_shade(para, 'F6F8FA')
            _para_border(para)
            run = para.add_run(line if line else ' ')
            _set_run_font(run, size=9, code=True, color=RGBColor(0x24, 0x29, 0x2E))
        if caption:
            pc = self.doc.add_paragraph()
            pc.paragraph_format.space_before = Pt(2)
            pc.paragraph_format.space_after = Pt(8)
            run = pc.add_run(caption.replace('`', ''))
            _set_run_font(run, size=9, color=GREY)

    def note(self, text, label='注意'):
        para = self.doc.add_paragraph()
        para.paragraph_format.left_indent = Cm(0.3)
        para.paragraph_format.space_before = Pt(6)
        para.paragraph_format.space_after = Pt(8)
        para.paragraph_format.line_spacing = 1.3
        para.paragraph_format.keep_together = True
        _para_shade(para, 'FFF8E1')
        _para_border(para, color='E0A800', size='12')
        run = para.add_run(f'{label}　')
        _set_run_font(run, size=10, bold=True, color=RGBColor(0x8A, 0x5A, 0x00))
        self._rich(para, text, size=10)
        return para

    def tip(self, text):
        return self.note(text, label='口诀')

    def table(self, headers, rows, widths=None, font_size=9, header_fill='DCE6F1'):
        t = self.doc.add_table(rows=1, cols=len(headers))
        t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False

        # 固定表格布局 + 总宽度 100%，否则 Word 会按内容自动撑开、列宽设置失效
        tblPr = t._tbl.tblPr
        layout = OxmlElement('w:tblLayout')
        layout.set(qn('w:type'), 'fixed')
        tblPr.append(layout)
        tblW = OxmlElement('w:tblW')
        tblW.set(qn('w:w'), '5000')
        tblW.set(qn('w:type'), 'pct')
        tblPr.append(tblW)

        # 可用宽度：A4 21cm - 左 2.4 - 右 2.2 = 16.4cm；按比例缩放到这个宽度
        available = 16.4
        if widths:
            total = sum(widths)
            widths = [w * available / total for w in widths]
        else:
            widths = [available / len(headers)] * len(headers)

        hdr = t.rows[0].cells
        # 表头跨页重复
        trPr = t.rows[0]._tr.get_or_add_trPr()
        trPr.append(OxmlElement('w:tblHeader'))
        trPr.append(OxmlElement('w:cantSplit'))

        for i, h in enumerate(headers):
            hdr[i].text = ''
            para = hdr[i].paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.paragraph_format.space_after = Pt(2)
            para.paragraph_format.space_before = Pt(2)
            run = para.add_run(h)
            _set_run_font(run, size=font_size, bold=True, color=ACCENT)
            _shade(hdr[i]._tc.get_or_add_tcPr(), header_fill)

        for row in rows:
            tr = t.add_row()
            tr._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
            cells = tr.cells
            for i, val in enumerate(row):
                cells[i].text = ''
                para = cells[i].paragraphs[0]
                para.paragraph_format.space_after = Pt(2)
                para.paragraph_format.space_before = Pt(2)
                para.paragraph_format.line_spacing = 1.2
                self._rich(para, str(val), size=font_size)

        # 列宽必须逐单元格设置，并且同步 tblGrid，否则 LibreOffice/Word 会按等分渲染
        cols = t._tbl.tblGrid.findall(qn('w:gridCol'))
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
            if i < len(cols):
                cols[i].set(qn('w:w'), str(int(w * 567)))   # 1 cm = 567 twips

        # 表格后留白
        spacer = self.doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(2)
        spacer.paragraph_format.line_spacing = 0.6
        return t

    def pagebreak(self):
        self.doc.add_page_break()

    def spacer(self, pt=6):
        para = self.doc.add_paragraph()
        para.paragraph_format.space_after = Pt(pt)
        return para


def new_document():
    doc = Document()

    # 页面
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.2)

    # 正文样式
    style = doc.styles['Normal']
    style.font.name = CN_FONT
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), CN_FONT)
    style.paragraph_format.line_spacing = 1.35
    style.paragraph_format.space_after = Pt(6)

    # 页脚页码
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    fldChar1 = OxmlElement('w:fldChar'); fldChar1.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = ' PAGE '
    fldChar2 = OxmlElement('w:fldChar'); fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instr)
    run._r.append(fldChar2)
    _set_run_font(run, size=9, color=GREY)

    return doc
