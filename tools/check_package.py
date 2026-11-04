"""Verify individual downloads, integrated figures and the common report."""
import hashlib,json,re,subprocess,zipfile
from pathlib import Path
from urllib.parse import unquote,urlsplit
from pypdf import PdfReader
import pdfplumber
from lxml import etree
from lxml import html as html_parser
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'site'; DL=SITE/'downloads'
C=json.loads((ROOT/'content/course.json').read_text(encoding='utf-8'))
guide_text=json.dumps(C['guide'],ensure_ascii=False)
assert 'data/context.json' not in guide_text,'control file path does not match the individual archive'
assert 'Остатки и historical_order_total брать из своего context.json' not in guide_text,'context has no stock-total field'
control_forms=[b['code'] for s in C['guide'] for b in s['blocks'] if b.get('title')=='Форма контрольного файла']
assert len(control_forms)==1 and 'stock_total' in json.loads(control_forms[0]),'missing usable control-file form'
method=html_parser.fromstring((SITE/'lessons.html').read_bytes())
schema_parts=[]
for index,section in enumerate(C['guide'],1):
 if any(b.get('code_file')=='01_schema.sql' for b in section['blocks']):
  for pre in method.xpath(f'//article[@id="step-{index}"]//pre'):
   schema_parts.extend(pre.text_content().splitlines())
assert schema_parts==(ROOT/'project/01_schema.sql').read_text(encoding='utf-8').splitlines(),'rendered schema fragments overlap or omit source lines'
assert len(C['areas'])==30 and len({a['id'] for a in C['areas']})==30
for page in SITE.glob('*.html'):
 for link in re.findall(r'(?:href|src)="([^"]+)"',page.read_text(encoding='utf-8')):
  p=urlsplit(link)
  if not p.scheme and p.path:assert (page.parent/unquote(p.path)).exists(),(page.name,link)
for a in C['areas']:
 n=f'{a["id"]:02}'
 with zipfile.ZipFile(DL/f'variant-{n}.zip') as z:
  own=[p for p in z.namelist() if p.startswith('data/')]
  assert len(own)==6 and all(p.startswith(f'data/variant-{n}/') for p in own)
  for p in own:assert z.read(p)==(ROOT/p).read_bytes()
  assert all(p in z.namelist() for p in ['README.md','sql/','er/','checks/','docs/HANDOFF.md'])
  readme=z.read('README.md').decode('utf-8-sig')
  assert 'общего архива' not in readme,(n,'stale common-archive instruction')
  assert 'docs/HANDOFF.md' in readme,(n,'handoff location is not explicit')
with zipfile.ZipFile(DL/'demo-data.zip') as z:
 originals=[p for p in z.namelist() if p.endswith('.xlsx')]
 assert len(originals)==5
 for p in originals:assert z.read(p)==(ROOT/p).read_bytes()
assert not (DL/'source-materials.zip').exists()
figures=[b for s in C['guide'] for b in s['blocks'] if b['kind']=='image']
assert len(figures)>=45
for b in figures:
 source=ROOT/b['path'];w,h=Image.open(source).size;x,y,cw,ch=b.get('crop',[0,0,w,h])
 assert x>=0 and y>=0 and x+cw<=w+2 and y+ch<=h+2,b['path']
 assert (SITE/'assets/screenshots'/source.name).read_bytes()==source.read_bytes()
base=C['meta']['site_url'].rstrip('/')+'/downloads/'
for name in ['assignment.pdf','guide.pdf']:
 pdf=PdfReader(DL/name)
 links=[unquote(str(a.get_object().get('/A',{}).get('/URI',''))) for p in pdf.pages for a in p.get('/Annots',[])]
 for n in ['database-starter.zip','demo-data.zip','demo-solution.zip']:assert base+n in links,(name,n)
 assert all(len(p.extract_text().strip())>10 for p in pdf.pages)
 # Inspect the produced PDF: overflow can shrink the whole document even when
 # the CSS declares the right font sizes.
 with pdfplumber.open(DL/name) as rendered:
  first=rendered.pages[0]
  body=[c for c in first.chars if c['text'].strip() and 'GolosText' in c['fontname'] and abs(c['size']-10.5)<.03]
  assert len(body)>100,(name,'body was scaled away from the approved10.5pt profile')
  footer=[c for c in first.chars if c['text'].strip() and c['top']>first.height-45]
  assert ''.join(c['text'] for c in footer)=='1',(name,'missing page number')
  assert all('GolosText' in c['fontname'] and abs(c['size']-8)<.03 for c in footer),(name,'footer font or size')
  if name=='assignment.pdf':
   page_index=next(i for i,p in enumerate(pdf.pages) if 'Рисунок 1 ' in p.extract_text())
   caption=rendered.pages[page_index].search(r'Рисунок\s+1\s*—')[0]['chars']
   assert all('GolosText' in c['fontname'] and abs(c['size']-9.5)<.03 for c in caption),(name,'figure caption profile')
 if name=='assignment.pdf':
  for sql_name in ['01_schema.sql','02_staging.sql','03_import.sql','04_queries.sql','09_checks_walkthrough.sql']:
   assert base+sql_name in links,(name,'missing direct SQL link',sql_name)
  pdftext='\n'.join(p.extract_text() for p in pdf.pages)
  assert 'описанным выше способом' not in pdftext,'stale forward reference to the ER workflow'
  for n in range(1,len(figures)+1):assert f'Рисунок {n} ' in pdftext
  assert sum(len(p.images) for p in pdf.pages)>=35
 else:
  for a in C['areas']:assert base+f'variant-{a["id"]:02}.zip' in links
 print(name,len(pdf.pages),'pages')
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
report=ROOT/'forms/Отчет о выполнении.docx'
with zipfile.ZipFile(report) as z:
 xml=etree.fromstring(z.read('word/document.xml'))
 text=lambda e:''.join(e.xpath('.//w:t/text()',namespaces=ns))
 captions=[text(p) for p in xml.xpath('//w:p',namespaces=ns) if text(p).startswith('Рисунок ')]
 expected=[x for s in C['report']['sections'] for x in s['screenshots']]
 assert len(captions)==len(expected)==18
 assert captions==[f'Рисунок {i} — {s.lower()}' for i,s in enumerate(expected,1)]
 fields=' '.join(xml.xpath('//w:instrText/text()',namespaces=ns))
 assert 'TOC' not in fields and fields.count('SEQ Рисунок')==18 and fields.count('REF pm11_fig_')==18
 for tag in ['tag','id']:
  ids=xml.xpath(f'//w:sdtPr/w:{tag}/@w:val',namespaces=ns);assert len(ids)==len(set(ids))
 slots=xml.xpath('//w:sdt[w:sdtPr/w:tag[starts-with(@w:val,"pm11_figure_")]]',namespaces=ns)
 assert len(slots)==18
 for slot in slots:
  row=slot.xpath('ancestor::w:tr',namespaces=ns)[0];height=row.find('w:trPr/w:trHeight',ns)
  assert height.get('{'+ns['w']+'}hRule','atLeast')=='atLeast' and int(height.get('{'+ns['w']+'}val'))>=3400
 assert not xml.xpath('//w:drawing',namespaces=ns)
 assert all(t in text(xml) for t in ['Исходные условия','Выполнение и проверка','Итоговая проверка и сдача','Ссылка на репозиторий проекта'])
assert (DL/report.name).read_bytes()==report.read_bytes()
assert hashlib.sha256((ROOT/'forms/template/Отчет о выполнении.docx').read_bytes()).hexdigest()=='5b91286458395ae589ded859021f287ce50cca1148cc5b29226b6fb1cb5373c4'
for name in ['05_order.sql','06_checks.sql','07_roles.sql','08_adaptation.sql']:
 original=subprocess.check_output(['git','show','3e1f649585d48772c451b34ea9cb1e8e51811e2c:project/'+name],cwd=ROOT)
 assert (ROOT/'project/reference'/name).read_bytes()==original
for name,value in json.loads((SITE/'manifest.json').read_text(encoding='utf-8'))['files'].items():
 assert hashlib.sha256((SITE/name).read_bytes()).hexdigest()==value,name
print('PASS: 30 isolated variants, five original XLSX,',len(figures),'integrated figures, 18 report slots, retained SQL, links and hashes')
