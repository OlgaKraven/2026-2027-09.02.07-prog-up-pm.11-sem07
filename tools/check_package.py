"""Check deliverable links, retained explanations, PDFs and report slots."""
import hashlib,json,re,subprocess,zipfile
from pathlib import Path
from urllib.parse import unquote,urlsplit
from pypdf import PdfReader
from docx import Document
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site'
C=json.loads((ROOT/'content/course.json').read_text(encoding='utf-8'))
assert len(C['areas'])==30 and len({a['id'] for a in C['areas']})==30
missing=[]
for page in SITE.glob('*.html'):
 for link in re.findall(r'(?:href|src)="([^"]+)"',page.read_text(encoding='utf-8')):
  parts=urlsplit(link)
  if parts.scheme or not parts.path:continue
  if not (page.parent/unquote(parts.path)).exists():missing.append((page.name,link))
assert not missing,missing
with zipfile.ZipFile(SITE/'downloads/source-materials.zip') as z:
 for a in C['areas']:
  for n in ['products','sizes','stock','users','orders']:assert f'data/variant-{a["id"]:02}/{n}.csv' in z.namelist()
 assert len([n for n in z.namelist() if n.endswith('.xlsx')])==5
required=[C['meta']['site_url'].rstrip('/')+'/downloads/'+n for n in ['source-materials.zip','database-starter.zip','demo-solution.zip']]
for name in ['assignment.pdf','guide.pdf']:
 pdf=PdfReader(SITE/'downloads'/name)
 links=[str(a.get_object().get('/A',{}).get('/URI','')) for p in pdf.pages for a in p.get('/Annots',[])]
 for u in required:assert u in links,(name,u)
 assert all(len(p.extract_text().strip())>10 for p in pdf.pages)
 print(name,len(pdf.pages),'pages; direct archives clickable')
doc=Document(ROOT/'forms/Форма отчёта УП ПМ.11.docx')
captions=[p.text for p in doc.paragraphs if p.text.startswith('Рисунок ')]
assert len(doc.tables)==len(captions)==14
assert captions==[f'Рисунок {i} — {s}' for i,s in enumerate([x for s in C['report']['sections'] for x in s['screenshots']],1)]
assert 'Ссылка на репозиторий проекта' in '\n'.join(p.text for p in doc.paragraphs)
for name in ['05_order.sql','06_checks.sql','07_roles.sql','08_adaptation.sql']:
 original=subprocess.check_output(['git','show','3e1f649585d48772c451b34ea9cb1e8e51811e2c:project/'+name],cwd=ROOT)
 assert (ROOT/'project/reference'/name).read_bytes()==original
manifest=json.loads((SITE/'manifest.json').read_text(encoding='utf-8'))['files']
for name,value in manifest.items():assert hashlib.sha256((SITE/name).read_bytes()).hexdigest()==value,name
print('PASS: 30 areas, 5 XLSX, all local links, retained sources, 14 Word slots and captions, manifest')
