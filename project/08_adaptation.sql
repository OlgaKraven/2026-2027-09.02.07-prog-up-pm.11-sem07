-- === Добавление проверяемого свойства в собственную копию демонстрации
ALTER TABLE product ADD warranty_months INT NULL CHECK(warranty_months>0);
UPDATE product SET warranty_months=12 WHERE product_id=1;
SELECT product_id,name,warranty_months FROM product ORDER BY product_id;
-- NULL означает, что значение не задано. Ноль должен вызвать ошибку CHECK.
-- === Справочник со своей сущностью
CREATE TABLE season (
 season_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;
INSERT INTO season(name) VALUES('Всесезонный');
ALTER TABLE product ADD season_id BIGINT NULL,
 ADD FOREIGN KEY(season_id) REFERENCES season(season_id) ON DELETE RESTRICT;
UPDATE product SET season_id=1 WHERE product_id=1;
SELECT p.name,s.name AS season FROM product p LEFT JOIN season s USING(season_id);
-- === Связь многие-ко-многим без списка в одной ячейке
CREATE TABLE usage_type (
 usage_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;
CREATE TABLE product_usage (
 product_id BIGINT NOT NULL,usage_id BIGINT NOT NULL,
 PRIMARY KEY(product_id,usage_id),
 FOREIGN KEY(product_id) REFERENCES product(product_id) ON DELETE RESTRICT,
 FOREIGN KEY(usage_id) REFERENCES usage_type(usage_id) ON DELETE RESTRICT
) ENGINE=InnoDB;
INSERT INTO usage_type(name) VALUES('Прогулка'),('Повседневное использование');
INSERT INTO product_usage(product_id,usage_id) VALUES(1,1),(1,2);
SELECT p.name,u.name AS usage_name FROM product_usage pu
JOIN product p USING(product_id) JOIN usage_type u USING(usage_id);
-- === Агрегат и сохранение сущностей без заказов
SELECT p.product_id,p.name,SUM(i.available) AS stock,
 SUM(i.available>0) AS available_sizes
FROM product p JOIN stock_item i USING(product_id)
GROUP BY p.product_id,p.name HAVING SUM(i.available)<5
ORDER BY stock,p.product_id;
SELECT c.customer_id,c.login,COUNT(o.order_id) AS orders
FROM customer c LEFT JOIN sales_order o USING(customer_id)
GROUP BY c.customer_id,c.login ORDER BY c.customer_id;
-- === Цена проданной единицы с учётом количества
SELECT p.product_id,p.name,SUM(l.quantity) AS units,
 SUM(l.quantity*l.unit_price) AS revenue,
 SUM(l.quantity*l.unit_price)/SUM(l.quantity) AS average_unit_price
FROM order_line l JOIN stock_item i USING(item_id)
JOIN product p USING(product_id) GROUP BY p.product_id,p.name;
