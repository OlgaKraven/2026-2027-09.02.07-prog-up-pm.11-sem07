-- === Исправление двух подтверждённых несогласованностей ДЭ
UPDATE stg_products
SET name=REPLACE(name,CONVERT(0xC2A0 USING utf8mb4),' ');
UPDATE stg_stock SET name='Черные туфли в классическом стиле — база для деловых образов'
WHERE name='Черные туфли в классическом стиле' AND manufacturer='Барбари';
UPDATE stg_orders SET name='Черные туфли в классическом стиле — база для деловых образов'
WHERE name='Черные туфли в классическом стиле' AND manufacturer='Барбари';
-- === Поиск дублей и отсутствующих связей
SELECT name,manufacturer,COUNT(*) AS duplicates
FROM stg_products GROUP BY name,manufacturer HAVING COUNT(*)>1;
SELECT s.name,s.manufacturer,s.size FROM stg_stock s
LEFT JOIN stg_products p ON p.name=s.name AND p.manufacturer=s.manufacturer
LEFT JOIN stg_sizes z ON z.label=s.size
WHERE p.name IS NULL OR z.label IS NULL;
SELECT o.order_id,o.full_name FROM stg_orders o
WHERE (SELECT COUNT(*) FROM stg_users u WHERE
 CONCAT_WS(' ',u.last_name,u.first_name,NULLIF(u.patronymic,''))=o.full_name)<>1;
SELECT order_id FROM stg_orders GROUP BY order_id
HAVING COUNT(DISTINCT ordered_at)>1 OR COUNT(DISTINCT full_name)>1;
SELECT o.order_id,o.name,o.size FROM stg_orders o
LEFT JOIN stg_stock s ON s.name=o.name AND s.manufacturer=o.manufacturer AND s.size=o.size
LEFT JOIN stg_products p ON p.name=o.name AND p.manufacturer=o.manufacturer AND p.category=o.category
WHERE s.name IS NULL OR p.name IS NULL;
SELECT name,manufacturer,size,COUNT(*) AS duplicates FROM stg_stock
GROUP BY name,manufacturer,size HAVING COUNT(*)>1;
SELECT login,COUNT(*) AS duplicates FROM stg_users GROUP BY login HAVING COUNT(*)>1;
SELECT order_id,name,manufacturer,size,COUNT(*) AS duplicates FROM stg_orders
GROUP BY order_id,name,manufacturer,size HAVING COUNT(*)>1;
SELECT name,price FROM stg_products
WHERE price IS NULL OR price NOT REGEXP '^[0-9]+([.][0-9]{1,2})?$' OR CAST(price AS DECIMAL(12,2))<=0;
SELECT name,available FROM stg_stock
WHERE available IS NULL OR available NOT REGEXP '^[0-9]+$';
SELECT order_id,quantity,unit_price FROM stg_orders
WHERE quantity IS NULL OR quantity NOT REGEXP '^[1-9][0-9]*$'
OR unit_price IS NULL OR unit_price NOT REGEXP '^[0-9]+([.][0-9]{1,2})?$'
OR CAST(unit_price AS DECIMAL(12,2))<=0;
-- Продолжайте только при пустых результатах диагностических запросов выше.
-- === Справочники и товары внутри одной транзакции
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
COMMIT;
