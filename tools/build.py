"""Build the learning site and downloadable source packages."""
import csv,hashlib,html,json,re,shutil,sys,zipfile
from PIL import Image
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'site'; DL=SITE/'downloads'
C=json.loads((ROOT/'content/course.json').read_text(encoding='utf-8'))
E=json.loads((ROOT/'content/extensions.json').read_text(encoding='utf-8'))
BASE=C['meta']['site_url'].rstrip('/')+'/'
DL.mkdir(parents=True,exist_ok=True)
FIGURE=0
def esc(s):return html.escape(str(s),quote=True)
def put(name,text):(SITE/name).write_text(text,encoding='utf-8',newline='\n')
def text(s):
 return ''.join('<p>'+re.sub(r'https?://[^\s<]+',lambda m:'<a href="'+m[0]+'">'+m[0]+'</a>',esc(p)).replace('\n','<br>')+'</p>' for p in s.split('\n\n'))
def head(kicker,title,subtitle=''):
 return '<header class="chapter"><p class="kicker">'+esc(kicker)+'</p><h1>'+esc(title)+'</h1>'+('<p>'+esc(subtitle)+'</p>' if subtitle else '')+'</header>'
def buttons(items):return '<div class="actions">'+''.join('<a class="button" href="'+esc(p)+'">'+esc(t)+'</a>' for p,t in items)+'</div>'
def card(b,n):
 global FIGURE
 if b['kind']=='image':
  path=b['path']; source=ROOT/path
  if not source.exists():raise FileNotFoundError(source)
  dest=SITE/'assets/screenshots'/source.name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,dest)
  FIGURE+=1
  iw,ih=Image.open(source).size
  x,y,w,h=b.get('crop',[0,0,iw,ih])
  if x<0 or y<0 or x+w>iw+2 or y+h>ih+2:raise ValueError((source.name,'invalid crop',b.get('crop'),(iw,ih)))
  style=f'aspect-ratio:{w}/{h};max-width:{b.get("display_mm",160)}mm'
  imgstyle=f'width:{iw/w*100:.6f}%;left:0;top:0;transform:translate({-x/iw*100:.8f}%,{-y/ih*100:.8f}%)'
  marks=''.join(f'<span class="screen-mark" style="left:{mx/w*100:.4f}%;top:{my/h*100:.4f}%;width:{mw/w*100:.4f}%;height:{mh/h*100:.4f}%"><b>{num}</b></span>' for num,mx,my,mw,mh in b.get('marks',[]))
  notes=b.get('notes',[])
  details=('<ol class="screen-notes">'+''.join('<li>'+esc(v)+'</li>' for v in notes)+'</ol>') if notes else text(b.get('text',''))
  return '<li class="illustration"><figure><a class="screen-original" href="assets/screenshots/'+esc(source.name)+'" aria-label="Открыть полный снимок: '+esc(b['title'])+'"><span class="screen-view" style="'+style+'"><img style="'+imgstyle+'" src="assets/screenshots/'+esc(source.name)+'" alt="'+esc(b.get('alt',b['title']))+'">'+marks+'</span></a><figcaption>Рисунок '+str(FIGURE)+' — '+esc(b['title'])+'</figcaption></figure>'+details+'</li>'
 if b['kind']=='code':
  if 'code' in b:raw=b['code']
  else:
   lines=(ROOT/'project'/b['code_file']).read_text(encoding='utf-8').splitlines()
   if 'code_lines' in b:
    lo,hi=b['code_lines'];assert 0<=lo<=hi<=len(lines);lines=lines[lo:hi]
   raw='\n'.join(lines)
  if b.get('code_file')=='01_schema.sql':
   statements=[];statement=[]
   for line in raw.splitlines():
    statement.append(line)
    if line.rstrip().endswith(';'):statements.append(statement);statement=[]
   if statement:statements.append(statement)
   chunks=[];chunk=[]
   for statement in statements:
    if chunk and len(chunk)+len(statement)>14:chunks.append(chunk);chunk=[]
    chunk.extend(statement)
   if chunk:chunks.append(chunk)
  else:chunks=[raw.splitlines()[i:i+14] for i in range(0,len(raw.splitlines()),14)]
  return ''.join(card(dict(kind='snippet',title=b['title']+(' · продолжение' if i else ''),text='\n'.join(ch)),str(n)+(f'.{i+1}' if len(chunks)>1 else '')) for i,ch in enumerate(chunks))
 inner='<pre><code>'+esc(b['text'])+'</code></pre>' if b['kind']=='snippet' else text(b.get('text',''))
 if b.get('check'):inner+='<p class="result"><strong>Проверка.</strong> '+esc(b['check'])+'</p>'
 return '<li class="step"><span class="number">'+str(n)+'</span><section class="card"><h3>'+esc(b['title'])+'</h3>'+inner+'</section></li>'
def chapter(s,n,anchor=''):
 blocks=[];idx=0
 for b in s['blocks']:
  if b['kind']!='image':idx+=1
  blocks.append(card(b,idx))
 return '<article class="lesson" id="'+anchor+'">'+head('ПМ.11 · Раздел '+str(n),s['title'])+'<ol class="route">'+''.join(blocks)+'</ol></article>'
def page(title,body,active='',script=''):
 nav='<a class="skip" href="#main">К содержанию</a><nav aria-label="Разделы практики">'+''.join('<a href="'+p+'"'+(' aria-current="page"' if p==active else '')+'>'+t+'</a>' for p,t in [('index.html','Задание'),('lessons.html','Методические рекомендации'),('areas.html','Предметные области'),('extensions.html','Для углубления')])+'</nav>'
 return '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+' — УП ПМ.11</title><link rel="icon" href="assets/favicon.svg"><link rel="stylesheet" href="assets/style.css"></head><body>'+nav+'<main id="main">'+body+'</main>'+script+'</body></html>'
assignment=''.join(chapter(s,i,'assignment-'+str(i)) for i,s in enumerate(C['assignment'],1))
links=[('database-starter.zip','Заготовка проекта'),('demo-data.zip','Исходные данные образца «Пара»'),('demo-solution.zip','Тестовый проект образца «Пара»')]
files=dict(title='Файлы и первый шаг',blocks=[
 dict(kind='text',title='Свой вариант',text='В списке предметных областей открыть карточку по своему порядковому номеру в списке группы. Скачать только variant-NN.zip по прямой ссылке этой карточки. В нём находятся пять собственных CSV, context.json, структура рабочей папки, карта полей и инструкция начала. Общий архив всех индивидуальных наборов не требуется.',check='Номер карточки совпадает с номером строки в списке своей группы.'),
 dict(kind='text',title='Заготовка и SQL образца',text='database-starter.zip содержит пустую структуру проекта и порядок работы. SQL образца 01_schema.sql — 04_queries.sql можно читать по прямым ссылкам ниже; по объяснениям подготовить собственные SQL. demo-solution.zip служит сверкой после собственной попытки. Отдельно создавать демонстрационную БД не требуется.'),
 dict(kind='text',title='Прямые ссылки на архивы',text='\n\n'.join(t+': '+BASE+'downloads/'+p for p,t in links),check='Тестовый проект — отдельный образец для сверки; его данные не заменяют свой вариант.'),
 dict(kind='text',title='SQL-файлы для чтения и подготовки собственной работы',text='\n\n'.join(label+': '+BASE+'downloads/'+name for name,label in [
  ('01_schema.sql','Схема образца: изучить перед созданием собственных таблиц'),
  ('02_staging.sql','Промежуточный слой: сохранить в sql до его создания'),
  ('03_import.sql','Технический помощник импорта: сохранить в sql и согласовать имена своих таблиц до защищённого переноса'),
  ('04_queries.sql','Контрольные представления и запросы: подготовить к проверке принятого импорта'),
  ('09_checks_walkthrough.sql','Проверочные запросы: изучить перед опытами на отдельной копии')]),check='Сохранить файл по нужной ссылке; в редакторе проверить его имя и содержимое до выполнения. Все SQL-файлы доступны из PDF отдельно от тестового проекта.'),
 dict(kind='text',title='Отчёт и документы',text='Бланк «Отчет о выполнении.docx» содержит три основных раздела, таблицы и места для собственных рисунков. Он выдаётся отдельно и входит в пакет EatDoners. Заполнить факты своей области и ссылку на репозиторий; подписи рисунков согласованы с презентацией.')])
material=chapter(files,'Файлы','files')+buttons([('downloads/'+p,t) for p,t in links]+[('downloads/Отчет о выполнении.docx','Отчет о выполнении · DOCX')]+[('downloads/'+p,p) for p in ['01_schema.sql','02_staging.sql','03_import.sql','04_queries.sql','09_checks_walkthrough.sql']])
method=''.join(chapter(s,'М.'+str(i),'step-'+str(i)) for i,s in enumerate(C['guide'],1))
toc='<section class="contents"><h2>Маршрут работы</h2><ol>'+''.join('<li><a href="#step-'+str(i)+'">'+esc(s['title'])+'</a></li>' for i,s in enumerate(C['guide'],1))+'</ol></section>'
literature=chapter(dict(title='Литература и документация',blocks=[dict(kind='text',title='Для углубления',text='\n\n'.join(C['literature']))]),'Источники')
hero=head('Учебная практика · 4 курс · 7 семестр','Разработка и импорт базы данных','Одна собственная схема, проверяемые исходные строки и сохранённая история заказов.')
put('index.html',page('Задание',hero+assignment+material+buttons([('lessons.html','Перейти к методике'),('downloads/assignment.pdf','Методические рекомендации · PDF'),('downloads/guide.pdf','Предметные области · PDF')]),'index.html'))
put('lessons.html',page('Методические рекомендации',head('ПМ.11 · Образец «Пара»','Методические рекомендации','Изучить приём на образце и выполнить действие сразу в своей БД.')+toc+method+literature,'lessons.html'))
def area(a):
 identity='<div class="identity"><p><strong>Индивидуальная работа</strong>'+esc(a['subject'])+'</p><p><strong>Образец — «Пара»</strong>Объясняет приёмы; отдельно повторять его не требуется.</p></div>'
 context=json.loads((ROOT/f'data/variant-{a["id"]:02}/context.json').read_text(encoding='utf-8'))
 data='<section class="data"><h2>Входные данные</h2><p>Папка data/variant-'+f'{a["id"]:02}'+'. Историческая сумма: '+str(context['historical_order_total'])+'.</p><table><thead><tr><th>Файл</th><th>Строк данных</th></tr></thead><tbody>'+''.join('<tr><td>'+name+'.csv</td><td>'+str(count)+'</td></tr>' for name,count in context['rows'].items())+'</tbody></table></section>'
 direct=BASE+f'downloads/variant-{a["id"]:02}.zip'
 standalone='<p class="variant-download"><strong>Комплект своего варианта:</strong><br><a href="'+esc(direct)+'">'+esc(direct)+'</a></p>'
 return '<article class="area" id="variant-'+str(a['id'])+'" data-variant="'+str(a['id'])+'">'+head('ПМ.11 · Вариант '+f'{a["id"]:02}',a['subject'])+identity+standalone+data+'<ol class="route">'+''.join(card(b,i) for i,b in enumerate(a['blocks'],1))+'</ol>'+buttons([(f'downloads/variant-{a["id"]:02}.zip','Скачать комплект своего варианта'),('downloads/Отчет о выполнении.docx','Отчет о выполнении'),('lessons.html#step-1','Начало методики')])+'</article>'
area_start=chapter(dict(title='Найти проект и данные своей области',blocks=[
 dict(kind='text',title='Скачать свой комплект',text='Найти свою фамилию в списке своей группы. В списке предметных областей открыть карточку с порядковым номером строки. Для строки 7 выбрать вариант 07 и скачать variant-07.zip. Если фамилии или номера нет, уточнить вариант у руководителя. После распаковки открыть data/variant-NN: пять CSV и context.json содержат собственные данные. Папки sql, er, docs и checks подготовлены для своей работы. Для примера 07 используется только комплект variant-07.zip.'),
 dict(kind='text',title='Прямые ссылки',text='\n\n'.join(t+': '+BASE+'downloads/'+p for p,t in links)),
 dict(kind='text',title='Начало и результат',text='В phpMyAdmin создать одну собственную БД pm11_vNN с utf8mb4_bin. Прочитать общее задание и идти по методике; названия и контрольные числа заменять значениями своего набора. Передать ER.pdf, SQL, данные, словарь, журнал, контрольные значения и заполненный отчёт. Дополнительные условия из раздела углубления не обязательны для сдачи.')]),'Начало')
areas=''.join(area(a) for a in C['areas'])
chooser='<div class="chooser"><label for="variant">Предметная область</label><select id="variant">'+''.join('<option value="'+str(a['id'])+'">'+esc(a['title'])+'</option>' for a in C['areas'])+'</select><button id="prev">Предыдущая</button><button id="next">Следующая</button><p id="position" aria-live="polite"></p></div>'
script='''<script>const choose=document.querySelector('#variant'),all=[...document.querySelectorAll('.area')];function show(n){n=Math.min(all.length,Math.max(1,Number(n)||1));choose.value=n;all.forEach(a=>a.hidden=Number(a.dataset.variant)!==n);document.querySelector('#prev').disabled=n===1;document.querySelector('#next').disabled=n===all.length;document.querySelector('#position').textContent=`Вариант ${n} из ${all.length}`;history.replaceState(null,'','#variant-'+n)}choose.addEventListener('change',()=>show(choose.value));document.querySelector('#prev').onclick=()=>show(Number(choose.value)-1);document.querySelector('#next').onclick=()=>show(Number(choose.value)+1);show(location.hash.split('-').pop());</script>'''
put('areas.html',page('Предметные области',area_start+chooser+areas,'areas.html',script))
optional=head('ПМ.11 · Дополнительное изучение','Для углубления','Эти разборы сохраняют подробный демонстрационный пример. Они не входят в обязательную сдачу схемы и импорта.')+buttons([('downloads/extensions.zip','Исходники и дополнительные разборы')])+''.join(chapter(s,'Д.'+str(i),'extra-'+str(i)) for i,s in enumerate(E['guide'],1))
optional+=head('Индивидуальные расширения','Дополнительные условия областей','Применять по отдельному заданию после принятия основного результата.')+''.join(chapter(dict(title=a['subject'],blocks=a['blocks']),'В.'+str(a['id'])) for a in E['areas'])
put('extensions.html',page('Для углубления',optional,'extensions.html'))
put('print-method.html',page('Методические рекомендации',hero+assignment+material+method+literature))
print_start=re.sub(r'<header class="chapter">.*?</header>','',area_start,count=1,flags=re.S)
put('print-areas.html',page('Предметные области',head('Учебная практика ПМ.11','Список предметных областей')+print_start+areas))
def archive(name,files):
 with zipfile.ZipFile(DL/name,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(set(files)):
   if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
if '--keep-downloads' not in sys.argv:
 archive('database-starter.zip',list((ROOT/'starter').rglob('*')))
 refs=[ROOT/'project'/n for n in ['INPUT_MAPPING.md','DATA_DICTIONARY.md','HANDOFF.md','SOURCE.md']]
 archive('demo-data.zip',list((ROOT/'data/demo').rglob('*'))+list((ROOT/'data/original').rglob('*'))+refs)
 archive('demo-solution.zip',list((ROOT/'project').rglob('*'))+list((ROOT/'data/demo').rglob('*')))
 archive('extensions.zip',list((ROOT/'project/reference').rglob('*'))+[ROOT/'content/extensions.json'])
 for a in C['areas']:
  with zipfile.ZipFile(DL/f'variant-{a["id"]:02}.zip','w',zipfile.ZIP_DEFLATED) as z:
   for p in sorted((ROOT/f'data/variant-{a["id"]:02}').glob('*')):
    if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
   z.write(ROOT/'starter/README.md','README.md')
   for d in ['sql','er','docs','checks']:z.writestr(d+'/',b'')
   for n in ['INPUT_MAPPING.md','DATA_DICTIONARY.md','HANDOFF.md']:z.write(ROOT/'project'/n,'docs/'+n)
 for p in (ROOT/'project').iterdir():
  if p.is_file():shutil.copy2(p,DL/p.name)
 report=ROOT/'forms/Отчет о выполнении.docx'
 if report.exists():shutil.copy2(report,DL/report.name)
 for legacy in ['source-materials.zip','report-template.docx','report-template.md']:
  target=DL/legacy
  if target.is_file():target.unlink()
manifest={p.relative_to(SITE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in SITE.rglob('*') if p.is_file() and p.name!='manifest.json'}
put('manifest.json',json.dumps(dict(schema_version=1,files=manifest),ensure_ascii=False,indent=2)+'\n')
print('Site and source packages prepared')
