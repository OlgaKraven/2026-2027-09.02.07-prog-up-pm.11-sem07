-- === Контроль до успешного оформления
SELECT COUNT(*) AS orders_before FROM sales_order;
SELECT item_id,available FROM stock_item WHERE item_id IN(1,2);
CALL place_order(1,'[{"item_id":1,"quantity":1},{"item_id":2,"quantity":1}]');
SELECT * FROM order_totals ORDER BY order_id DESC LIMIT 1;
SELECT item_id,available FROM stock_item WHERE item_id IN(1,2);
-- === Ошибка второй строки не сохраняет первую
CALL place_order(1,'[{"item_id":1,"quantity":1},{"item_id":2,"quantity":999999}]');
-- После ошибки отдельно выполните следующие запросы и сравните со снимком ДО вызова.
SELECT COUNT(*) AS orders_after_error FROM sales_order;
SELECT item_id,available FROM stock_item WHERE item_id IN(1,2);
-- === Ограничения: каждый блок выполняется отдельно
START TRANSACTION;
UPDATE stock_item SET available=-1 WHERE item_id=1;
ROLLBACK;
START TRANSACTION;
INSERT INTO stock_item(product_id,size_id,available) VALUES(999999,1,1);
ROLLBACK;
START TRANSACTION;
INSERT INTO customer(login,last_name,first_name,role_id)
SELECT login,last_name,first_name,role_id FROM customer LIMIT 1;
ROLLBACK;
