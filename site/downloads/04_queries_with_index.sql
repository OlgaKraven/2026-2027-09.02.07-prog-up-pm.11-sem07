-- === Представление каталога
CREATE VIEW catalog AS
SELECT i.item_id,p.name,c.name AS category,sc.name AS subcategory,
 m.name AS manufacturer,z.label AS size,i.available,p.price,p.image_path
FROM stock_item i JOIN product p USING(product_id)
JOIN subcategory sc USING(subcategory_id) JOIN category c USING(category_id)
JOIN manufacturer m USING(manufacturer_id) JOIN size z USING(size_id);
SELECT * FROM catalog ORDER BY name,size;
-- === Итоги из исторической цены
CREATE VIEW order_totals AS
SELECT o.order_id,o.ordered_at,
 CONCAT_WS(' ',c.last_name,c.first_name,NULLIF(c.patronymic,'')) AS customer,
 CAST(SUM(l.quantity*l.unit_price) AS DECIMAL(14,2)) AS total
FROM sales_order o JOIN customer c USING(customer_id)
JOIN order_line l USING(order_id)
GROUP BY o.order_id,o.ordered_at,c.customer_id,c.last_name,c.first_name,c.patronymic;
SELECT * FROM order_totals ORDER BY order_id;
-- === Состав заказа и контроль связей
SELECT l.order_id,k.name,k.manufacturer,k.size,l.quantity,l.unit_price,
 l.quantity*l.unit_price AS line_total
FROM order_line l JOIN catalog k USING(item_id) ORDER BY l.order_id,k.name;
SELECT COUNT(*) AS broken_links FROM order_line l
LEFT JOIN sales_order o USING(order_id) LEFT JOIN stock_item s USING(item_id)
WHERE o.order_id IS NULL OR s.item_id IS NULL;
-- === Индекс для истории клиента
CREATE INDEX ix_order_customer_date ON sales_order(customer_id,ordered_at);
EXPLAIN SELECT * FROM sales_order WHERE customer_id=1 ORDER BY ordered_at;
