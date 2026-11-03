-- Подтверждённые исправления образца; исходные файлы не изменяются.
INSERT IGNORE INTO import_issue
SELECT source_file,source_row,'name_nbsp','Неразрывный пробел в названии модели',
 'исправлено',name,REPLACE(name,CONVERT(0xC2A0 USING utf8mb4),' ')
FROM stg_products WHERE name LIKE CONCAT('%',CONVERT(0xC2A0 USING utf8mb4),'%');
UPDATE stg_products SET name=REPLACE(name,CONVERT(0xC2A0 USING utf8mb4),' ');
INSERT IGNORE INTO import_issue
SELECT source_file,source_row,'short_name','Подтверждённое сокращённое название образца',
 'исправлено',name,'Черные туфли в классическом стиле — база для деловых образов'
FROM stg_stock WHERE name='Черные туфли в классическом стиле' AND manufacturer='Барбари';
UPDATE stg_stock SET name='Черные туфли в классическом стиле — база для деловых образов'
WHERE name='Черные туфли в классическом стиле' AND manufacturer='Барбари';
INSERT IGNORE INTO import_issue
SELECT source_file,source_row,'short_name','Подтверждённое сокращённое название образца',
 'исправлено',name,'Черные туфли в классическом стиле — база для деловых образов'
FROM stg_orders WHERE name='Черные туфли в классическом стиле' AND manufacturer='Барбари';
UPDATE stg_orders SET name='Черные туфли в классическом стиле — база для деловых образов'
WHERE name='Черные туфли в классическом стиле' AND manufacturer='Барбари';
-- Готовый помощник проверки и переноса. Разработка процедур не является заданием.
DELIMITER //
CREATE OR REPLACE PROCEDURE import_checked()
BEGIN
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 IF (SELECT COUNT(*) FROM category)+(SELECT COUNT(*) FROM subcategory)+(SELECT COUNT(*) FROM manufacturer)+(SELECT COUNT(*) FROM size)+(SELECT COUNT(*) FROM product)+(SELECT COUNT(*) FROM stock_item)+(SELECT COUNT(*) FROM app_role)+(SELECT COUNT(*) FROM customer)+(SELECT COUNT(*) FROM sales_order)+(SELECT COUNT(*) FROM order_line) > 0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Target must be empty: use a fresh checking database';
 END IF;
 DELETE FROM import_issue WHERE disposition='отклонено';
 INSERT INTO import_issue(source_file,source_row,issue_code,reason) SELECT 'products.csv',1,'missing_data','Файл не загружен или не содержит записей' WHERE NOT EXISTS(SELECT 1 FROM stg_products);
 INSERT INTO import_issue(source_file,source_row,issue_code,reason) SELECT 'sizes.csv',1,'missing_data','Файл не загружен или не содержит записей' WHERE NOT EXISTS(SELECT 1 FROM stg_sizes);
 INSERT INTO import_issue(source_file,source_row,issue_code,reason) SELECT 'stock.csv',1,'missing_data','Файл не загружен или не содержит записей' WHERE NOT EXISTS(SELECT 1 FROM stg_stock);
 INSERT INTO import_issue(source_file,source_row,issue_code,reason) SELECT 'users.csv',1,'missing_data','Файл не загружен или не содержит записей' WHERE NOT EXISTS(SELECT 1 FROM stg_users);
 INSERT INTO import_issue(source_file,source_row,issue_code,reason) SELECT 'orders.csv',1,'missing_data','Файл не загружен или не содержит записей' WHERE NOT EXISTS(SELECT 1 FROM stg_orders);
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'product_key','Пустая категория, подкатегория, модель или производитель'
 FROM stg_products s WHERE COALESCE(TRIM(category),'')='' OR COALESCE(TRIM(subcategory),'')='' OR COALESCE(TRIM(name),'')='' OR COALESCE(TRIM(manufacturer),'')='';
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'product_duplicate','Повтор модели и производителя'
 FROM stg_products s WHERE (SELECT COUNT(*) FROM stg_products x WHERE x.name=s.name AND x.manufacturer=s.manufacturer)<>1;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'price','Цена модели должна быть положительным DECIMAL(12,2)'
 FROM stg_products s WHERE price IS NULL OR price NOT REGEXP '^[0-9]{1,10}([.][0-9]{1,2})?$' OR CAST(IF(price REGEXP '^[0-9]{1,10}([.][0-9]{1,2})?$',price,'0') AS DECIMAL(12,2))<=0;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'size_key','Пустая или повторная маркировка'
 FROM stg_sizes s WHERE COALESCE(TRIM(label),'')='' OR (SELECT COUNT(*) FROM stg_sizes x WHERE x.label=s.label)<>1;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'stock_link','Модель или маркировка не найдена однозначно'
 FROM stg_stock s WHERE (SELECT COUNT(*) FROM stg_products p WHERE p.name=s.name AND p.manufacturer=s.manufacturer)<>1 OR (SELECT COUNT(*) FROM stg_sizes z WHERE z.label=s.size)<>1;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'stock_duplicate','Повтор пары модель и маркировка'
 FROM stg_stock s WHERE (SELECT COUNT(*) FROM stg_stock x WHERE x.name=s.name AND x.manufacturer=s.manufacturer AND x.size=s.size)>1;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'available','Остаток должен быть целым числом от 0 до 2147483647'
 FROM stg_stock s WHERE available IS NULL OR available NOT REGEXP '^[0-9]{1,10}$' OR CAST(IF(available REGEXP '^[0-9]{1,10}$',available,'0') AS UNSIGNED)>2147483647;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'customer_key','Пустые данные клиента или повторный логин'
 FROM stg_users s WHERE COALESCE(TRIM(login),'')='' OR COALESCE(TRIM(last_name),'')='' OR COALESCE(TRIM(first_name),'')='' OR COALESCE(TRIM(role),'')='' OR (SELECT COUNT(*) FROM stg_users x WHERE x.login=s.login)<>1;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'order_customer','ФИО заказа не соответствует ровно одному клиенту'
 FROM stg_orders s WHERE (SELECT COUNT(*) FROM stg_users u WHERE CONCAT_WS(' ',u.last_name,u.first_name,NULLIF(u.patronymic,''))=s.full_name)<>1;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'order_item','Модель, категория или размерная позиция заказа не найдена однозначно'
 FROM stg_orders s WHERE (SELECT COUNT(*) FROM stg_products p WHERE p.name=s.name AND p.manufacturer=s.manufacturer AND p.category=s.category)<>1 OR (SELECT COUNT(*) FROM stg_stock x WHERE x.name=s.name AND x.manufacturer=s.manufacturer AND x.size=s.size)<>1;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'order_number','Номер заказа должен быть положительным целым числом до 10 цифр'
 FROM stg_orders s WHERE order_id IS NULL OR order_id NOT REGEXP '^[1-9][0-9]{0,9}$';
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'order_date','Неверный формат даты или несуществующий день месяца'
 FROM stg_orders s WHERE ordered_at IS NULL OR ordered_at NOT REGEXP '^[1-9][0-9]{3}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$' OR CASE WHEN ordered_at REGEXP '^[1-9][0-9]{3}-(0[1-9]|1[0-2])-' THEN CAST(SUBSTRING(ordered_at,9,2) AS UNSIGNED)>DAY(LAST_DAY(CONCAT(SUBSTRING(ordered_at,1,7),'-01'))) ELSE 0 END;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'order_header','У одного заказа разные даты или клиенты'
 FROM stg_orders s WHERE EXISTS(SELECT 1 FROM stg_orders x WHERE x.order_id=s.order_id AND (NOT(x.ordered_at<=>s.ordered_at) OR NOT(x.full_name<=>s.full_name)));
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'order_duplicate','Повтор размерной позиции внутри одного заказа'
 FROM stg_orders s WHERE (SELECT COUNT(*) FROM stg_orders x WHERE x.order_id=s.order_id AND x.name=s.name AND x.manufacturer=s.manufacturer AND x.size=s.size)>1;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'quantity_price','Количество и историческая цена должны быть положительными'
 FROM stg_orders s WHERE quantity IS NULL OR quantity NOT REGEXP '^[1-9][0-9]{0,9}$' OR CAST(IF(quantity REGEXP '^[1-9][0-9]{0,9}$',quantity,'0') AS UNSIGNED)>2147483647 OR unit_price IS NULL OR unit_price NOT REGEXP '^[0-9]{1,10}([.][0-9]{1,2})?$' OR CAST(IF(unit_price REGEXP '^[0-9]{1,10}([.][0-9]{1,2})?$',unit_price,'0') AS DECIMAL(12,2))<=0;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'text_length','Длина текста превышает размер поля схемы'
 FROM stg_products s WHERE CHAR_LENGTH(category)>120 OR CHAR_LENGTH(subcategory)>120 OR CHAR_LENGTH(name)>200 OR CHAR_LENGTH(manufacturer)>120 OR CHAR_LENGTH(image_path)>255;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'text_length','Длина текста превышает размер поля схемы'
 FROM stg_sizes s WHERE CHAR_LENGTH(label)>30;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'text_length','Длина текста превышает размер поля схемы'
 FROM stg_users s WHERE CHAR_LENGTH(last_name)>80 OR CHAR_LENGTH(first_name)>80 OR CHAR_LENGTH(patronymic)>80 OR CHAR_LENGTH(login)>80 OR CHAR_LENGTH(role)>80;
 INSERT INTO import_issue(source_file,source_row,issue_code,reason)
 SELECT s.source_file,s.source_row,'text_bytes','Описание или состав превышает размер TEXT'
 FROM stg_products s WHERE OCTET_LENGTH(description)>65535 OR OCTET_LENGTH(composition)>65535;
 IF EXISTS(SELECT 1 FROM import_issue WHERE disposition='отклонено') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Import rejected: read import_issue, correct staging, call import_checked again';
 END IF;
START TRANSACTION;
INSERT INTO category(name) SELECT DISTINCT category FROM stg_products ORDER BY category;
INSERT INTO subcategory(category_id,name)
SELECT DISTINCT c.category_id,p.subcategory FROM stg_products p
JOIN category c ON c.name=p.category ORDER BY c.category_id,p.subcategory;
INSERT INTO manufacturer(name) SELECT DISTINCT manufacturer FROM stg_products ORDER BY manufacturer;
INSERT INTO size(label) SELECT DISTINCT label FROM stg_sizes ORDER BY label;
INSERT INTO app_role(name) SELECT DISTINCT role FROM stg_users ORDER BY role;
INSERT INTO product(subcategory_id,manufacturer_id,name,image_path,description,composition,price)
SELECT sc.subcategory_id,m.manufacturer_id,p.name,COALESCE(p.image_path,''),
 COALESCE(p.description,''),COALESCE(p.composition,''),CAST(p.price AS DECIMAL(12,2))
FROM stg_products p JOIN category c ON c.name=p.category
JOIN subcategory sc ON sc.category_id=c.category_id AND sc.name=p.subcategory
JOIN manufacturer m ON m.name=p.manufacturer ORDER BY p.name,p.manufacturer;
-- === Остатки, клиенты и исторические заказы
INSERT INTO stock_item(product_id,size_id,available)
SELECT p.product_id,z.size_id,CAST(s.available AS SIGNED)
FROM stg_stock s JOIN manufacturer m ON m.name=s.manufacturer
JOIN product p ON p.name=s.name AND p.manufacturer_id=m.manufacturer_id
JOIN size z ON z.label=s.size ORDER BY p.product_id,z.size_id;
INSERT INTO customer(login,last_name,first_name,patronymic,role_id)
SELECT u.login,u.last_name,u.first_name,COALESCE(u.patronymic,''),r.role_id
FROM stg_users u JOIN app_role r ON r.name=u.role ORDER BY u.login;
INSERT INTO sales_order(order_id,customer_id,ordered_at)
SELECT DISTINCT CAST(o.order_id AS UNSIGNED),c.customer_id,CAST(o.ordered_at AS DATETIME)
FROM stg_orders o JOIN customer c ON
 CONCAT_WS(' ',c.last_name,c.first_name,NULLIF(c.patronymic,''))=o.full_name;
INSERT INTO order_line(order_id,item_id,quantity,unit_price)
SELECT CAST(o.order_id AS UNSIGNED),s.item_id,CAST(o.quantity AS SIGNED),
 CAST(o.unit_price AS DECIMAL(12,2))
FROM stg_orders o JOIN manufacturer m ON m.name=o.manufacturer
JOIN product p ON p.name=o.name AND p.manufacturer_id=m.manufacturer_id
JOIN size z ON z.label=o.size
JOIN stock_item s ON s.product_id=p.product_id AND s.size_id=z.size_id;
 IF (SELECT COUNT(*) FROM product)<>(SELECT COUNT(*) FROM stg_products) OR
 (SELECT COUNT(*) FROM size)<>(SELECT COUNT(*) FROM stg_sizes) OR
 (SELECT COUNT(*) FROM stock_item)<>(SELECT COUNT(*) FROM stg_stock) OR
 (SELECT COUNT(*) FROM customer)<>(SELECT COUNT(*) FROM stg_users) OR
 (SELECT COUNT(*) FROM order_line)<>(SELECT COUNT(*) FROM stg_orders) OR
 (SELECT COUNT(*) FROM sales_order)<>(SELECT COUNT(DISTINCT order_id) FROM stg_orders) THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Row count mismatch; target transaction rolled back';
 END IF;
 COMMIT;
END//
DELIMITER ;
CALL import_checked();
SELECT source_file,source_row,issue_code,reason,disposition,old_value,new_value
FROM import_issue ORDER BY source_file,source_row,issue_code;
