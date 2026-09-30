-- === Групповые роли MariaDB для учебной БД pm11_demo
CREATE ROLE pm11_reader;
CREATE ROLE pm11_order;
CREATE ROLE pm11_operator;
GRANT SELECT ON pm11_demo.catalog TO pm11_reader;
GRANT SELECT ON pm11_demo.order_totals TO pm11_reader;
GRANT SELECT ON pm11_demo.catalog TO pm11_order;
GRANT SELECT ON pm11_demo.order_totals TO pm11_order;
GRANT EXECUTE ON PROCEDURE pm11_demo.place_order TO pm11_order;
-- === Эксплуатация и резервное копирование
GRANT SELECT,SHOW VIEW,TRIGGER,EVENT,LOCK TABLES ON pm11_demo.* TO pm11_operator;
GRANT UPDATE(available) ON pm11_demo.stock_item TO pm11_operator;
GRANT UPDATE(price) ON pm11_demo.product TO pm11_operator;
-- Личные учётные записи создайте в phpMyAdmin с собственными паролями.
-- Назначьте каждой её роль и выполните SET DEFAULT ROLE имя_роли FOR 'логин'@'localhost'.
-- Замените pm11_demo именем своей БД до выполнения; роли создаются один раз на сервере.
