"""Adapt a copy of the common Word master to the PM.11 evidence stages."""
from copy import deepcopy
from pathlib import Path
import hashlib,json,shutil,zipfile
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Mm
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml import OxmlElement
import report_template_components as parts
from illustrate_course import REPORT_STAGES

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/'forms/template/Отчет о выполнении.docx'
OUTPUT=ROOT/'forms/Отчет о выполнении.docx'
before=hashlib.sha256(MASTER.read_bytes()).hexdigest()
shutil.copy2(MASTER,OUTPUT)
doc=Document(OUTPUT)

def content_text(node):return ''.join(t.text or '' for t in node.iter(qn('w:t')))
def set_control(tag,value):
    for control in doc.element.xpath('.//w:sdt'):
        found=control.find('w:sdtPr/w:tag',doc.element.nsmap)
        if found is not None and found.get(qn('w:val'))==tag:
            texts=list(control.find(qn('w:sdtContent')).iter(qn('w:t')))
            texts[0].text=value
            for t in texts[1:]:t.text=''

set_control('institution','АНО ВО «СИНЕРГИЯ»')
set_control('practice_name','УП ПМ.11 «Разработка, администрирование и защита баз данных»')

def label_rows(table,labels,tag):
    original=deepcopy(table.rows[1]._tr)
    while len(table.rows)<len(labels)+1:table._tbl.append(deepcopy(original))
    while len(table.rows)>len(labels)+1:table._tbl.remove(table.rows[-1]._tr)
    for i,label in enumerate(labels,1):
        for j,cell in enumerate(table.rows[i].cells):
            controls=cell._tc.xpath('.//w:sdt')
            for k,sdt in enumerate(controls):
                pr=sdt.find(qn('w:sdtPr'))
                pr.find(qn('w:tag')).set(qn('w:val'),f'{tag}_{i}_{j}_{k}')
                pr.find(qn('w:id')).set(qn('w:val'),str(20000+i*100+j*10+k+sum(map(ord,tag))))
                ts=list(sdt.find(qn('w:sdtContent')).iter(qn('w:t')))
                for t in ts:t.text=''
                ts[0].text=label if j==0 else '____________'
            if j==0 and not controls:
                ts=cell._tc.xpath('.//w:t')
                if ts:
                    ts[0].text=label
                    for t in ts[1:]:t.text=''

label_rows(doc.tables[0],['Предметная область и номер варианта','Пять исходных CSV','Ссылка на свой комплект','Контрольный файл context.json'],'inputs')
label_rows(doc.tables[1],['XAMPP и Apache','MariaDB или MySQL','phpMyAdmin','Текстовый редактор','Microsoft Word','Браузер'],'environment')
label_rows(doc.tables[2],['Магазин «Пара»','pm11_demo_visual','data/demo','expected.json','Маркировки и названия образца','Контрольные значения образца'],'mapping')
label_rows(doc.tables[-1],['ER и ограничения','Пять CSV и координаты строк','Журнал и отказ переноса','Исправление и успешный повтор','Счётчики, остатки и сумма истории','Историческая цена','Три отказа ограничений','Чистое развёртывание','Доступность проекта и состав сдачи'],'final')

# Keep the substitution table with its caption on a fresh page.
map_caption=doc.tables[2]._tbl.getprevious()
if map_caption.tag==qn('w:p'):
    pr=map_caption.find(qn('w:pPr'))
    if pr is None:pr=OxmlElement('w:pPr');map_caption.insert(0,pr)
    pr.append(OxmlElement('w:pageBreakBefore'))
# The final check labels need enough width to avoid three-line rows.
t=doc.tables[-1];t.autofit=False
for col,width in zip(t.columns,[65,32,33,30]):col.width=Mm(width)
for row in t.rows:
    row.height=Mm(10);row.height_rule=WD_ROW_HEIGHT_RULE.AT_LEAST
    for cell,width in zip(row.cells,[65,32,33,30]):cell.width=Mm(width)

body=doc.element.body
children=list(body)
start=next(i for i,e in enumerate(children) if content_text(e)=='Этап выполнения работы')
end=next(i for i,e in enumerate(children) if content_text(e)=='Итоговая проверка и сдача')
anchor=children[end]
for e in children[start:end]:body.remove(e)

# The copied master already owns the styles, numbering, section and footer.
# New blocks reuse its exact named components; only document.xml changes here.
parts.CONTROL_ID=10000
fig=0
new=[]
for index,(title,hint,captions) in enumerate(REPORT_STAGES,1):
    first=len(list(body))-1
    parts.heading(doc,title,level=2,new_page=index>1)
    doc.add_paragraph(hint)
    parts.response(doc,'Исходные данные и ожидаемый результат',f's{index}_initial',1 if index==5 else 2)
    parts.response(doc,'Выполненные действия',f's{index}_actions',2 if index==5 else 3)
    parts.response(doc,'Фактический результат и проверка',f's{index}_actual',1 if index==5 else 2)
    if index==5:
        table=parts.data_table(doc,'сверка исходных и итоговых значений',4,
            ['Показатель','Ожидалось','Получено','Вывод'],[48,37,37,38],'counts')
        label_rows(table,['Модели','Маркировки','Размерные позиции','Клиенты','Заказы','Строки заказа','Сумма остатков','Сумма истории'],'counts')
        for row in table.rows:
            row.height=Mm(10);row.height_rule=WD_ROW_HEIGHT_RULE.AT_LEAST
    if index==6:
        table=parts.data_table(doc,'цена и история до и после изменения',5,
            ['Состояние','Текущая цена','Сумма истории'],[55,50,55],'prices')
        label_rows(table,['До изменения','После изменения','После ROLLBACK'],'prices')
    parts.response(doc,'Вывод по этапу и объяснение расхождений',f's{index}_conclusion',1 if index==5 else 2)
    doc.add_page_break()
    p=doc.add_paragraph()
    p.add_run('Подтверждения этапа приведены на рис. ')
    for j,caption in enumerate(captions):
        if j:p.add_run(', ')
        parts.field(p,f'REF pm11_fig_{fig+j+1} \\h',str(fig+j+1))
    p.add_run('. Вставить собственные результаты и сохранить подписи.')
    for j,caption in enumerate(captions):
        if j and j%2==0:doc.add_page_break()
        fig+=1
        parts.figure_slot(doc,caption,f'pm11_figure_{fig}',fig,f'pm11_fig_{fig}')
    generated=list(body)[first:-1]
    for e in generated:
        body.remove(e)
        anchor.addprevious(e)

for p in doc.paragraphs:
    for b in p._p.findall(qn('w:bookmarkStart')):
        name=b.get(qn('w:name'),'')
        if name.startswith('pm11_fig_'):
            old_id=b.get(qn('w:id'));new_id=str(1000+int(name.rsplit('_',1)[1]))
            b.set(qn('w:id'),new_id)
            for end_b in p._p.findall(qn('w:bookmarkEnd')):
                if end_b.get(qn('w:id'))==old_id:end_b.set(qn('w:id'),new_id)
for control_id,control in enumerate(doc.element.xpath('.//w:sdt'),30000):
    control.find('w:sdtPr/w:id',doc.element.nsmap).set(qn('w:val'),str(control_id))
doc.core_properties.title='Отчет о выполнении'
doc.core_properties.subject='УП ПМ.11'
doc.core_properties.author=doc.core_properties.last_modified_by=''
doc.core_properties.comments=doc.core_properties.keywords=''
doc.save(OUTPUT)

# Keep every untouched master package part byte-for-byte.
with zipfile.ZipFile(OUTPUT) as z:edited={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(MASTER) as z:original={n:z.read(n) for n in z.namelist()}
allowed={'word/document.xml','docProps/core.xml'}
with zipfile.ZipFile(OUTPUT,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in original.items():z.writestr(name,edited[name] if name in allowed else data)
assert hashlib.sha256(MASTER.read_bytes()).hexdigest()==before
with zipfile.ZipFile(OUTPUT) as z:
    for n,data in original.items():
        if n not in allowed:assert z.read(n)==data,n
source=dict(master_sha256=before,main_sections=['Исходные условия','Выполнение и проверка','Итоговая проверка и сдача'],stages=[dict(title=t,prompt=p,screenshots=s) for t,p,s in REPORT_STAGES])
(ROOT/'content/report-structure.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUTPUT,fig,'figure slots')
