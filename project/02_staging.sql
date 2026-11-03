-- При импорте CSV явно указать только исходные поля без source_file и source_row.
CREATE TABLE stg_products (
 category TEXT,subcategory TEXT,image_path TEXT,name TEXT,manufacturer TEXT,description TEXT,composition TEXT,price TEXT,
 source_file VARCHAR(80) NOT NULL DEFAULT 'products.csv',
 source_row BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
) ENGINE=InnoDB AUTO_INCREMENT=2;
CREATE TABLE stg_sizes (
 label TEXT,
 source_file VARCHAR(80) NOT NULL DEFAULT 'sizes.csv',
 source_row BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
) ENGINE=InnoDB AUTO_INCREMENT=2;
CREATE TABLE stg_stock (
 name TEXT,manufacturer TEXT,size TEXT,available TEXT,
 source_file VARCHAR(80) NOT NULL DEFAULT 'stock.csv',
 source_row BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
) ENGINE=InnoDB AUTO_INCREMENT=2;
CREATE TABLE stg_users (
 last_name TEXT,first_name TEXT,patronymic TEXT,login TEXT,role TEXT,
 source_file VARCHAR(80) NOT NULL DEFAULT 'users.csv',
 source_row BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
) ENGINE=InnoDB AUTO_INCREMENT=2;
CREATE TABLE stg_orders (
 order_id TEXT,ordered_at TEXT,full_name TEXT,category TEXT,name TEXT,manufacturer TEXT,size TEXT,quantity TEXT,unit_price TEXT,
 source_file VARCHAR(80) NOT NULL DEFAULT 'orders.csv',
 source_row BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
) ENGINE=InnoDB AUTO_INCREMENT=2;
CREATE TABLE import_issue (
 source_file VARCHAR(80) NOT NULL, source_row BIGINT UNSIGNED NOT NULL,
 issue_code VARCHAR(40) NOT NULL, reason TEXT NOT NULL,
 disposition VARCHAR(20) NOT NULL DEFAULT 'отклонено',
 old_value TEXT NULL, new_value TEXT NULL,
 PRIMARY KEY(source_file,source_row,issue_code)
) ENGINE=InnoDB;
SELECT s.source_file,s.source_row,s.name,s.manufacturer
FROM stg_stock s LEFT JOIN stg_products p
 ON p.name=s.name AND p.manufacturer=s.manufacturer WHERE p.name IS NULL;
