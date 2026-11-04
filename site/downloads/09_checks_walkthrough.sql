-- Выполнять только отдельные указанные блоки на проверочной копии.
-- Ожидаемые ошибки прерывают пакет, поэтому весь файл сразу не запускать.

-- Счётчики промежуточного слоя
SELECT 'products.csv' AS source, COUNT(*) AS rows_loaded,
 MIN(source_row) AS first_row FROM stg_products
UNION ALL SELECT 'sizes.csv',COUNT(*),MIN(source_row) FROM stg_sizes
UNION ALL SELECT 'stock.csv',COUNT(*),MIN(source_row) FROM stg_stock
UNION ALL SELECT 'users.csv',COUNT(*),MIN(source_row) FROM stg_users
UNION ALL SELECT 'orders.csv',COUNT(*),MIN(source_row) FROM stg_orders;

-- Контроль принятой БД
SELECT (SELECT COUNT(*) FROM product) AS models,
 (SELECT COUNT(*) FROM size) AS sizes,
 (SELECT COUNT(*) FROM stock_item) AS positions,
 (SELECT COUNT(*) FROM customer) AS customers,
 (SELECT COUNT(*) FROM sales_order) AS orders,
 (SELECT COUNT(*) FROM order_line) AS order_lines,
 (SELECT SUM(available) FROM stock_item) AS stock_total,
 (SELECT SUM(quantity*unit_price) FROM order_line) AS history_total;

-- Историческая цена: весь блок от START до последнего SELECT целиком
START TRANSACTION;
SET @pid := (SELECT s.product_id FROM stock_item s
 JOIN order_line l USING(item_id) ORDER BY l.order_id,l.item_id LIMIT 1);
SELECT 'before' AS phase,price AS current_price,
 (SELECT SUM(quantity*unit_price) FROM order_line) AS history_total
FROM product WHERE product_id=@pid;
UPDATE product SET price=price+17 WHERE product_id=@pid;
SELECT 'after' AS phase,price AS current_price,
 (SELECT SUM(quantity*unit_price) FROM order_line) AS history_total
FROM product WHERE product_id=@pid;
ROLLBACK;
SELECT 'restored' AS phase,price AS current_price,
 (SELECT SUM(quantity*unit_price) FROM order_line) AS history_total
FROM product WHERE product_id=@pid;

-- Опыт 1: ожидается #1062
INSERT INTO stock_item(product_id,size_id,available)
SELECT product_id,size_id,available FROM stock_item ORDER BY item_id LIMIT 1;

-- Опыт 2: ожидается #4025
UPDATE stock_item SET available=-1 ORDER BY item_id LIMIT 1;

-- Опыт 3: ожидается #1452
INSERT INTO stock_item(product_id,size_id,available)
SELECT MAX(product_id)+1000,(SELECT MIN(size_id) FROM size),0 FROM product;

-- Допустимый опыт: весь блок целиком
START TRANSACTION;
SELECT item_id,available FROM stock_item ORDER BY item_id LIMIT 1;
UPDATE stock_item SET available=available+1 ORDER BY item_id LIMIT 1;
SELECT item_id,available FROM stock_item ORDER BY item_id LIMIT 1;
ROLLBACK;
