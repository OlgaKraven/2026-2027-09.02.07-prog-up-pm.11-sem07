"""Export the student report form to Word; requires python-docx and Node marked."""
import json
import os
import pathlib
import subprocess
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'content/report-template.md'
OUTPUT = ROOT / 'forms/Форма отчёта УП ПМ.11.docx'

parser = "const fs=require('node:fs'); const {marked}=require('marked'); process.stdout.write(JSON.stringify(marked.lexer(fs.readFileSync(0,'utf8'))));"
parsed = subprocess.run([os.environ.get('NODE_BINARY', 'node'), '-e', parser],
                        input=re.sub(r'_{25,}', '_' * 24, SOURCE.read_text(encoding='utf-8')), text=True,
                        encoding='utf-8', capture_output=True, check=True)
tokens = json.loads(parsed.stdout)
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.left_margin, sec.right_margin = Mm(30), Mm(20)
sec.top_margin, sec.bottom_margin = Mm(20), Mm(20)
sec.footer_distance = Mm(10)

for name in ['Normal', 'Title', 'Heading 1', 'Heading 2', 'Heading 3', 'TOC Heading', 'TOC 1', 'TOC 2']:
    try:
        style = doc.styles[name]
    except KeyError:
        style = doc.styles.add_style(name, 1)
    style.font.name = 'Times New Roman'
    style.font.size = Pt(14)
    style.font.color.rgb = RGBColor(0, 0, 0)
    fonts = style.element.get_or_add_rPr().get_or_add_rFonts()
    for attr in list(fonts.attrib):
        del fonts.attrib[attr]
    for attr in ['ascii', 'hAnsi', 'eastAsia', 'cs']:
        fonts.set(qn('w:' + attr), 'Times New Roman')
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.first_line_indent = Mm(12.5)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.widow_control = True
    for tag in ['w:autoRedefine', 'w:pBdr']:
        for node in style.element.findall('.//' + qn(tag)):
            node.getparent().remove(node)

for name in ['Title', 'Heading 1', 'TOC Heading']:
    style = doc.styles[name]
    style.font.size = Pt(16)
    style.font.bold = True
    style.font.all_caps = True
    style.paragraph_format.first_line_indent = Mm(0)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style.paragraph_format.space_before = Pt(12)
    style.paragraph_format.space_after = Pt(12)
    style.paragraph_format.keep_with_next = True

caption_style = doc.styles['Caption']
caption_style.font.name = 'Times New Roman'
caption_style.font.size = Pt(12)
caption_style.font.italic = False
caption_style.font.color.rgb = RGBColor(0, 0, 0)
fonts = caption_style.element.get_or_add_rPr().get_or_add_rFonts()
for attr in list(fonts.attrib): del fonts.attrib[attr]
for attr in ['ascii', 'hAnsi', 'eastAsia', 'cs']: fonts.set(qn('w:' + attr), 'Times New Roman')
caption_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption_style.paragraph_format.first_line_indent = Mm(0)
caption_style.paragraph_format.line_spacing = 1
caption_style.paragraph_format.space_before = Pt(6)
caption_style.paragraph_format.space_after = Pt(12)

footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.paragraph_format.first_line_indent = Mm(0)
footer.paragraph_format.line_spacing = 1
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)

def add_inline(p, parts):
    for t in parts:
        if t['type'] in ['text', 'escape', 'codespan']:
            p.add_run(t.get('text', ''))
        elif t['type'] in ['strong', 'em', 'del']:
            before = len(p.runs)
            add_inline(p, t['tokens'])
            for run in p.runs[before:]:
                if t['type'] == 'strong': run.bold = True
                elif t['type'] == 'em': run.italic = True
                else: run.font.strike = True
        elif t['type'] == 'br':
            p.add_run().add_break()
        else:
            raise ValueError('Unsupported inline token: ' + t['type'])

body_started = False
for token in tokens:
    if token['type'] == 'space':
        continue
    if token['type'] == 'heading':
        if token['depth'] == 1:
            p = doc.add_paragraph(style='Title')
        else:
            if not body_started:
                doc.add_page_break()
                doc.add_paragraph('СОДЕРЖАНИЕ', style='TOC Heading')
                p = doc.add_paragraph()
                toc = OxmlElement('w:fldSimple')
                toc.set(qn('w:instr'), 'TOC \\o "1-2" \\h \\z \\u')
                p._p.append(toc)
                doc.add_page_break()
                body_started = True
            p = doc.add_paragraph(style='Heading ' + str(token['depth'] - 1))
        add_inline(p, token['tokens'])
    elif token['type'] == 'paragraph':
        if token.get('text') == 'МЕСТО ДЛЯ СКРИНШОТА':
            table = doc.add_table(rows=1, cols=1)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False
            table.columns[0].width = Mm(160)
            table.rows[0].height = Mm(60)
            table.rows[0].height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
            cant_split = OxmlElement('w:cantSplit')
            table.rows[0]._tr.get_or_add_trPr().append(cant_split)
            table.cell(0, 0).vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            borders = OxmlElement('w:tblBorders')
            for edge in ['top', 'left', 'bottom', 'right']:
                border = OxmlElement('w:' + edge)
                for attr, value in [('val','single'), ('sz','6'), ('color','808080')]: border.set(qn('w:' + attr), value)
                borders.append(border)
            table._tbl.tblPr.append(borders)
            p = table.cell(0, 0).paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Mm(0)
            p.paragraph_format.keep_with_next = True
            p.add_run('МЕСТО ДЛЯ СКРИНШОТА').font.size = Pt(12)
        else:
            p = doc.add_paragraph(style='Caption' if token.get('text','').startswith('Рисунок ') else None)
            add_inline(p, token['tokens'])
    else:
        raise ValueError('Unsupported block token: ' + token['type'])

for index, paragraph in enumerate(doc.paragraphs):
    if paragraph.style.name == 'Normal' and paragraph.text.strip():
        following = doc.paragraphs[index + 1] if index + 1 < len(doc.paragraphs) else None
        paragraph.paragraph_format.keep_with_next = paragraph.text.startswith('На рис.') or bool(following and following.style.name == 'Normal' and following.text.strip() and not paragraph.text.startswith('Получено'))
        if '_' in paragraph.text:
            paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

doc.core_properties.author = ''
doc.core_properties.last_modified_by = ''
doc.core_properties.title = 'Отчёт по учебной практике ПМ.11'
doc.core_properties.subject = 'Форма для заполнения по индивидуальному варианту'
doc.core_properties.comments = ''
OUTPUT.parent.mkdir(exist_ok=True)
doc.save(OUTPUT)
print(OUTPUT)

