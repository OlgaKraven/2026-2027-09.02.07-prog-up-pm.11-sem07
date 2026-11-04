"""Create the editable report source and the source/data reference documents."""
import csv,json
from pathlib import Path
import openpyxl
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'content/course.json').read_text(encoding='utf-8'))
files=[('Products_import.xlsx','products.csv','stg_products','category,subcategory,image_path,name,manufacturer,description,composition,price','category, subcategory, manufacturer, product'),('Sizes_import.xlsx','sizes.csv','stg_sizes','label','size'),('Stock_Items_import.xlsx','stock.csv','stg_stock','name,manufacturer,size,available','stock_item'),('Users_import.xlsx','users.csv','stg_users','last_name,first_name,patronymic,login,role','app_role, customer'),('Orders_import.xlsx','orders.csv','stg_orders','order_id,ordered_at,full_name,category,name,manufacturer,size,quantity,unit_price','sales_order, order_line')]
mapping=['# От исходных XLSX к учебным CSV','','Образец — магазин «Пара». Оригиналы находятся в data/original, CSV — в data/demo. Для индивидуальной работы используются только data/variant-NN. Порядок записей сохранён; source_row=2 обозначает первую запись после заголовка XLSX и CSV, а не физическую строку текста с возможными переносами внутри кавычек.','']
for xlsx,csvname,table,columns,target in files:
 wb=openpyxl.load_workbook(ROOT/'data/original'/xlsx,data_only=True,read_only=True)
 sheet=wb.active; rows=list(sheet.values)
 mapping += [f'## {xlsx}',f'Лист: {sheet.title}. Строк данных: {len(rows)-1}. CSV: {csvname}. Промежуточная таблица: {table}. Назначение: {target}.','','| Заголовок XLSX | Поле CSV |','| --- | --- |']
 mapping += [f'| {a} | {b} |' for a,b in zip(rows[0],columns.split(','))]
 mapping += ['','Даты приведены к YYYY-MM-DD HH:MM:SS; числа — с десятичной точкой; пустое отчество и путь изображения допускают пустую строку. Маркировки сохраняются строками. Кириллица и исходные несовпадения названий сохранены.','']
mapping += ['## Контроль преобразований','','31 модель, 35 маркировок, 92 размерные позиции, 20 клиентов, 30 строк 10 заказов. Сумма остатков — 1274. Историческая сумма — 341770.00; она вычисляется из количества и цены Orders_import.xlsx. Текущая цена Products_import.xlsx не подменяет цену покупки.','','В шести текстовых ячейках Products_import.xlsx удалены внешние пробелы или завершающие переносы: строки 11, 12, 27, 32 — Описание; строка 20 — Состав; строка 25 — Наименование товара. Внутренний неразрывный пробел сохранён для диагностики. tools/convert_sources.py воспроизводит преобразование и проверяет все значения пяти CSV, а не только количество записей.','','Справочники категорий, подкатегорий, производителей и ролей получаются из уникальных значений. Несколько строк Orders_import.xlsx с одним номером дают один sales_order; каждая исходная строка сохраняется в order_line. Ключ размерной позиции сопоставляется по модели, производителю и маркировке. ФИО должно определять ровно одного клиента.','','Исправления: неразрывный пробел в названии модели и сокращённое название «Черные туфли в классическом стиле» производителя «Барбари». SQL сохраняет координаты, причину, старое и новое значение в import_issue. Исходные файлы не перезаписываются.']
(ROOT/'project/INPUT_MAPPING.md').write_text('\n'.join(mapping)+'\n',encoding='utf-8')

meanings={
'category':('Категория','category_id — PK; name — уникальное непустое название.'),
'subcategory':('Подкатегория','subcategory_id — PK; category_id — FK category; name — название. Пара category_id,name уникальна.'),
'manufacturer':('Производитель','manufacturer_id — PK; name — уникальное название.'),
'size':('Маркировка','size_id — PK; label — уникальная строковая маркировка, включая буквенные размеры.'),
'product':('Модель','product_id — PK; subcategory_id и manufacturer_id — FK. name — модель; image_path — относительный путь; description — описание; composition — состав; price — текущая положительная цена DECIMAL(12,2). Пара name,manufacturer_id уникальна.'),
'stock_item':('Размерная позиция','item_id — PK; product_id и size_id — FK; available — целый неотрицательный остаток. Пара product_id,size_id уникальна.'),
'app_role':('Роль клиента в исходной системе','role_id — PK; name — уникальное название роли. Не является серверной учётной записью СУБД.'),
'customer':('Клиент','customer_id — PK; login — уникальный логин; last_name,first_name — фамилия и имя; patronymic — отчество или пустая строка; role_id — FK app_role. В исходниках нет пароля клиента.'),
'sales_order':('Исторический заказ','order_id — PK, номер из источника; customer_id — FK; ordered_at — дата и время заказа. Общая сумма вычисляется из строк.'),
'order_line':('Историческая строка','order_id и item_id образуют составной PK и являются FK. quantity — положительное целое; unit_price — положительная цена покупки DECIMAL(12,2), независимая от текущей product.price.')}
dictionary=['# Словарь полей демонстрационной модели','','PK — первичный ключ; FK — внешний ключ. Полные типы и ограничения находятся в 01_schema.sql. Для своей схемы сохранить этот документ с уточнениями предметной области.','']
for table,(title,desc) in meanings.items():dictionary += [f'## {table} — {title}',desc,'']
dictionary += ['## Промежуточный слой и журнал','Пять stg_таблиц повторяют поля CSV как TEXT до проверки. source_file — имя источника; source_row — номер исходной записи с учётом заголовка, начинается с 2. import_issue хранит source_file, source_row, issue_code, reason, disposition, old_value, new_value. Одна строка может иметь несколько разных причин; число отклонённых записей считают по различным координатам.','', '## Правила удаления','RESTRICT сохраняет используемые справочники, модели, позиции и клиентов. CASCADE действует только от заголовка заказа к его строкам; он не возвращает остатки. Создание и удаление новых заказов не являются заданием обязательной части.']
(ROOT/'project/DATA_DICTIONARY.md').write_text('\n'.join(dictionary)+'\n',encoding='utf-8')
handoff='''# Передача базы данных

## Состав

- sql/01_schema.sql, 02_staging.sql, 03_import.sql, 04_queries.sql собственной схемы;
- data/variant-NN — пять исходных CSV своего варианта и context.json;
- er/ER.pdf — предметные таблицы с атрибутами, ключами и связями;
- docs/DATA_DICTIONARY.md и INPUT_MAPPING.md — поля и происхождение данных;
- checks/import-issues.csv — полный журнал после принятого импорта;
- checks/rejections-before.csv — отклонения до исправления;
- checks/control.json — ожидаемые и фактические счётчики и суммы;
- README.md — точный порядок развёртывания и имя собственной БД;
- Отчет о выполнении.docx — заполненный отчёт со ссылкой на репозиторий.

## Чистое развёртывание

Создать свободную собственную БД utf8mb4_bin. Выполнить 01_schema.sql и 02_staging.sql по одному разу. Импортировать пять CSV в stg_таблицы с явным списком исходных полей; не загружать source_file и source_row из CSV. Выполнить полный 03_import.sql. При отклонении прочитать журнал, решить причины и повторить CALL import_checked(); только после исправления. Выполнить 04_queries.sql. Сравнить числа, суммы и связи с checks/control.json. Сопоставить ER.pdf со схемой. Не использовать абсолютные пути другого компьютера.

До новых операций сохранить принятую контрольную копию. Пакет передаёт готовую схему и импорт; повторное проектирование этих таблиц не является условием дальнейшего использования. Процедура place_order и расширения в основной пакет не требуются.

## Контрольный файл

Указать объект, исходное число и итоговое число для product, size, stock_item, customer, sales_order, order_line. Указать сумму available, историческую сумму quantity * unit_price, число отклонённых координат и решения. При группировке исходных строк в заголовки заказов объяснить отличие числа строк от числа заказов. Для демонстрации ориентиры: 31,35,92,20,10,30; остатки 1274; история 341770.00. Для своего варианта использовать собственные значения context.json.
'''
(ROOT/'project/HANDOFF.md').write_text(handoff,encoding='utf-8')

print('Source references prepared. Report is authored by tools/build_report.py from the common master.')
