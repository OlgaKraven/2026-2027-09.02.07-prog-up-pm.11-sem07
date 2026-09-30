-- === Промежуточный слой исходных значений
CREATE TABLE stg_products (
 category TEXT,subcategory TEXT,image_path TEXT,name TEXT,
 manufacturer TEXT,description TEXT,composition TEXT,price TEXT
) ENGINE=InnoDB;
CREATE TABLE stg_sizes (label TEXT) ENGINE=InnoDB;
CREATE TABLE stg_stock (
 name TEXT,manufacturer TEXT,size TEXT,available TEXT
) ENGINE=InnoDB;
CREATE TABLE stg_users (
 last_name TEXT,first_name TEXT,patronymic TEXT,login TEXT,role TEXT
) ENGINE=InnoDB;
CREATE TABLE stg_orders (
 order_id TEXT,ordered_at TEXT,full_name TEXT,category TEXT,name TEXT,
 manufacturer TEXT,size TEXT,quantity TEXT,unit_price TEXT
) ENGINE=InnoDB;
-- === Отчёт о несогласованных названиях до исправления
SELECT s.name,s.manufacturer FROM stg_stock s
LEFT JOIN stg_products p ON p.name=s.name AND p.manufacturer=s.manufacturer
WHERE p.name IS NULL;
