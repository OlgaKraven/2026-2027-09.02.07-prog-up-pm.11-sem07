"""Correct the practice type in a practice-specific copy of the supplied form."""
import argparse
from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
P=argparse.ArgumentParser();P.add_argument('source');P.add_argument('output');P.add_argument('--kind',choices=['attestation','assignment','explanation'],default='attestation');A=P.parse_args()
d=Document(A.source);changed=0
def paragraphs(parent):
 yield from parent.paragraphs
 for table in parent.tables:
  for row in table.rows:
   for cell in row.cells:yield from paragraphs(cell)
replacements=[]
if A.kind=='attestation':replacements=[('производственной','учебной'),('Производственной','Учебной'),('группы_______по','группы {{ГРУППА}} по')]
if A.kind=='assignment':replacements=[('Оформить справку, заверенную подписью и печатью (при наличии) ответственного лица от Профильной организации, содержащую сведения о прохождении практики.','Оформить отдельный отчёт DOCX с результатами своей работы, местами для рисунков и ссылкой на репозиторий проекта.')]
for p in paragraphs(d):
 for old,new in replacements:
  while old in p.text:
   start=p.text.index(old);end=start+len(old);offset=0;parts=[]
   for run in p.runs:
    rstart=offset;offset+=len(run.text)
    if rstart<end and offset>start:parts.append((run,rstart,offset))
   if not parts:raise ValueError('Text without editable runs')
   if len(parts)==1:
    run,lo,hi=parts[0];run.text=run.text[:start-lo]+new+run.text[end-lo:]
   else:
    first,lo,_=parts[0];last,llo,_=parts[-1]
    first.text=first.text[:start-lo]+new
    for run,_,_ in parts[1:-1]:run.text=''
    last.text=last.text[end-llo:]
   changed+=1
compat=d.settings.element.find(qn('w:compat'))
if compat is None:compat=OxmlElement('w:compat');d.settings.element.append(compat)
if compat.find(qn('w:doNotExpandShiftReturn')) is None:compat.append(OxmlElement('w:doNotExpandShiftReturn'))
out=Path(A.output);out.parent.mkdir(parents=True,exist_ok=True);d.save(out)
print('Corrected occurrences:',changed)
