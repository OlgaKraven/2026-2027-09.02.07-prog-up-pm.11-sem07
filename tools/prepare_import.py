"""Build the transparent validation and import helper for the demonstration."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
old=subprocess.check_output(['git','show','3e1f649585d48772c451b34ea9cb1e8e51811e2c:project/03_import.sql'],cwd=ROOT).decode('utf-8').replace('\r\n','\n')
tables={
'products':'category TEXT,subcategory TEXT,image_path TEXT,name TEXT,manufacturer TEXT,description TEXT,composition TEXT,price TEXT',
'sizes':'label TEXT',
'stock':'name TEXT,manufacturer TEXT,size TEXT,available TEXT',
'users':'last_name TEXT,first_name TEXT,patronymic TEXT,login TEXT,role TEXT',
'orders':'order_id TEXT,ordered_at TEXT,full_name TEXT,category TEXT,name TEXT,manufacturer TEXT,size TEXT,quantity TEXT,unit_price TEXT'}
stg='-- При импорте CSV явно указать только исходные поля без source_file и source_row.\n'
for name,cols in tables.items():
 stg+=f"CREATE TABLE stg_{name} (\n {cols},\n source_file VARCHAR(80) NOT NULL DEFAULT '{name}.csv',\n source_row BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY\n) ENGINE=InnoDB AUTO_INCREMENT=2;\n"
stg+='''CREATE TABLE import_issue (
 source_file VARCHAR(80) NOT NULL, source_row BIGINT UNSIGNED NOT NULL,
 issue_code VARCHAR(40) NOT NULL, reason TEXT NOT NULL,
 disposition VARCHAR(20) NOT NULL DEFAULT 'отклонено',
 old_value TEXT NULL, new_value TEXT NULL,
 PRIMARY KEY(source_file,source_row,issue_code)
) ENGINE=InnoDB;
SELECT s.source_file,s.source_row,s.name,s.manufacturer
FROM stg_stock s LEFT JOIN stg_products p
 ON p.name=s.name AND p.manufacturer=s.manufacturer WHERE p.name IS NULL;
'''
(ROOT/'project/02_staging.sql').write_text(stg,encoding='utf-8')

checks=[
('products','product_key','Пустая категория, подкатегория, модель или производитель',"COALESCE(TRIM(category),'')='' OR COALESCE(TRIM(subcategory),'')='' OR COALESCE(TRIM(name),'')='' OR COALESCE(TRIM(manufacturer),'')=''"),
('products','product_duplicate','Повтор модели и производителя',"(SELECT COUNT(*) FROM stg_products x WHERE x.name=s.name AND x.manufacturer=s.manufacturer)<>1"),
('products','price','Цена модели должна быть положительным DECIMAL(12,2)',"price IS NULL OR price NOT REGEXP '^[0-9]{1,10}([.][0-9]{1,2})?$' OR CAST(IF(price REGEXP '^[0-9]{1,10}([.][0-9]{1,2})?$',price,'0') AS DECIMAL(12,2))<=0"),
('sizes','size_key','Пустая или повторная маркировка',"COALESCE(TRIM(label),'')='' OR (SELECT COUNT(*) FROM stg_sizes x WHERE x.label=s.label)<>1"),
('stock','stock_link','Модель или маркировка не найдена однозначно',"(SELECT COUNT(*) FROM stg_products p WHERE p.name=s.name AND p.manufacturer=s.manufacturer)<>1 OR (SELECT COUNT(*) FROM stg_sizes z WHERE z.label=s.size)<>1"),
('stock','stock_duplicate','Повтор пары модель и маркировка',"(SELECT COUNT(*) FROM stg_stock x WHERE x.name=s.name AND x.manufacturer=s.manufacturer AND x.size=s.size)>1"),
('stock','available','Остаток должен быть целым числом от 0 до 2147483647',"available IS NULL OR available NOT REGEXP '^[0-9]{1,10}$' OR CAST(IF(available REGEXP '^[0-9]{1,10}$',available,'0') AS UNSIGNED)>2147483647"),
('users','customer_key','Пустые данные клиента или повторный логин',"COALESCE(TRIM(login),'')='' OR COALESCE(TRIM(last_name),'')='' OR COALESCE(TRIM(first_name),'')='' OR COALESCE(TRIM(role),'')='' OR (SELECT COUNT(*) FROM stg_users x WHERE x.login=s.login)<>1"),
('orders','order_customer','ФИО заказа не соответствует ровно одному клиенту',"(SELECT COUNT(*) FROM stg_users u WHERE CONCAT_WS(' ',u.last_name,u.first_name,NULLIF(u.patronymic,''))=s.full_name)<>1"),
('orders','order_item','Модель, категория или размерная позиция заказа не найдена однозначно',"(SELECT COUNT(*) FROM stg_products p WHERE p.name=s.name AND p.manufacturer=s.manufacturer AND p.category=s.category)<>1 OR (SELECT COUNT(*) FROM stg_stock x WHERE x.name=s.name AND x.manufacturer=s.manufacturer AND x.size=s.size)<>1"),
('orders','order_number','Номер заказа должен быть положительным целым числом до 10 цифр',"order_id IS NULL OR order_id NOT REGEXP '^[1-9][0-9]{0,9}$'"),
('orders','order_date','Неверный формат даты или несуществующий день месяца',"ordered_at IS NULL OR ordered_at NOT REGEXP '^[1-9][0-9]{3}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$' OR CASE WHEN ordered_at REGEXP '^[1-9][0-9]{3}-(0[1-9]|1[0-2])-' THEN CAST(SUBSTRING(ordered_at,9,2) AS UNSIGNED)>DAY(LAST_DAY(CONCAT(SUBSTRING(ordered_at,1,7),'-01'))) ELSE 0 END"),
('orders','order_header','У одного заказа разные даты или клиенты',"EXISTS(SELECT 1 FROM stg_orders x WHERE x.order_id=s.order_id AND (NOT(x.ordered_at<=>s.ordered_at) OR NOT(x.full_name<=>s.full_name)))"),
('orders','order_duplicate','Повтор размерной позиции внутри одного заказа',"(SELECT COUNT(*) FROM stg_orders x WHERE x.order_id=s.order_id AND x.name=s.name AND x.manufacturer=s.manufacturer AND x.size=s.size)>1"),
('orders','quantity_price','Количество и историческая цена должны быть положительными',"quantity IS NULL OR quantity NOT REGEXP '^[1-9][0-9]{0,9}$' OR CAST(IF(quantity REGEXP '^[1-9][0-9]{0,9}$',quantity,'0') AS UNSIGNED)>2147483647 OR unit_price IS NULL OR unit_price NOT REGEXP '^[0-9]{1,10}([.][0-9]{1,2})?$' OR CAST(IF(unit_price REGEXP '^[0-9]{1,10}([.][0-9]{1,2})?$',unit_price,'0') AS DECIMAL(12,2))<=0")]
sql='''-- Подтверждённые исправления образца; исходные файлы не изменяются.
INSERT IGNORE INTO import_issue
SELECT source_file,source_row,'name_nbsp','Неразрывный пробел в названии модели',
 'исправлено',name,REPLACE(name,CONVERT(0xC2A0 USING utf8mb4),' ')
FROM stg_products WHERE name LIKE CONCAT('%',CONVERT(0xC2A0 USING utf8mb4),'%');
UPDATE stg_products SET name=REPLACE(name,CONVERT(0xC2A0 USING utf8mb4),' ');
'''
for name in ['stock','orders']:
 sql+=f"""INSERT IGNORE INTO import_issue
SELECT source_file,source_row,'short_name','Подтверждённое сокращённое название образца',
 'исправлено',name,'Черные туфли в классическом стиле — база для деловых образов'
FROM stg_{name} WHERE name='Черные туфли в классическом стиле' AND manufacturer='Барбари';
UPDATE stg_{name} SET name='Черные туфли в классическом стиле — база для деловых образов'
WHERE name='Черные туфли в классическом стиле' AND manufacturer='Барбари';
"""
sql+='''-- Готовый помощник проверки и переноса. Разработка процедур не является заданием.
DELIMITER //
CREATE OR REPLACE PROCEDURE import_checked()
BEGIN
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 IF '''+'+'.join(f'(SELECT COUNT(*) FROM {t})' for t in ['category','subcategory','manufacturer','size','product','stock_item','app_role','customer','sales_order','order_line'])+''' > 0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Target must be empty: use a fresh checking database';
 END IF;
 DELETE FROM import_issue WHERE disposition='отклонено';
'''
for table in tables:
 sql+=f" INSERT INTO import_issue(source_file,source_row,issue_code,reason) SELECT '{table}.csv',1,'missing_data','Файл не загружен или не содержит записей' WHERE NOT EXISTS(SELECT 1 FROM stg_{table});\n"
limits={'products':{'category':120,'subcategory':120,'name':200,'manufacturer':120,'image_path':255},'sizes':{'label':30},'users':{'last_name':80,'first_name':80,'patronymic':80,'login':80,'role':80}}
for table,fields in limits.items():
 condition=' OR '.join(f'CHAR_LENGTH({name})>{limit}' for name,limit in fields.items())
 checks.append((table,'text_length','Длина текста превышает размер поля схемы',condition))
checks.append(('products','text_bytes','Описание или состав превышает размер TEXT','OCTET_LENGTH(description)>65535 OR OCTET_LENGTH(composition)>65535'))
for table,code,reason,condition in checks:
 sql+=f" INSERT INTO import_issue(source_file,source_row,issue_code,reason)\n SELECT s.source_file,s.source_row,'{code}','{reason}'\n FROM stg_{table} s WHERE {condition};\n"
sql+=''' IF EXISTS(SELECT 1 FROM import_issue WHERE disposition='отклонено') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Import rejected: read import_issue, correct staging, call import_checked again';
 END IF;
'''
sql+=old[old.index('START TRANSACTION;'):old.rindex('COMMIT;')]
comparisons=[('product','products'),('size','sizes'),('stock_item','stock'),('customer','users'),('order_line','orders')]
sql+=' IF '+' OR\n '.join(f'(SELECT COUNT(*) FROM {target})<>(SELECT COUNT(*) FROM stg_{src})' for target,src in comparisons)+''' OR
 (SELECT COUNT(*) FROM sales_order)<>(SELECT COUNT(DISTINCT order_id) FROM stg_orders) THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Row count mismatch; target transaction rolled back';
 END IF;
 COMMIT;
END//
DELIMITER ;
CALL import_checked();
SELECT source_file,source_row,issue_code,reason,disposition,old_value,new_value
FROM import_issue ORDER BY source_file,source_row,issue_code;
'''
(ROOT/'project/03_import.sql').write_text(sql,encoding='utf-8')
q=subprocess.check_output(['git','show','3e1f649585d48772c451b34ea9cb1e8e51811e2c:project/04_queries.sql'],cwd=ROOT).decode('utf-8').replace('\r\n','\n')
(ROOT/'project/04_queries_with_index.sql').write_text(q,encoding='utf-8')
q=q[:q.index('-- === Индекс')]
q+='\n-- Контрольные счётчики до новых операций\n'+'\nUNION ALL '.join(f"SELECT '{t}' AS object_name,COUNT(*) AS rows_count FROM {t}" for t in ['product','size','stock_item','customer','sales_order','order_line'])+';\nSELECT SUM(available) AS available_total FROM stock_item;\nSELECT SUM(total) AS historical_total FROM order_totals;\n'
(ROOT/'project/04_queries.sql').write_text(q,encoding='utf-8')
print('Import SQL prepared')
