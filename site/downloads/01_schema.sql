-- === Справочники и третья нормальная форма
CREATE TABLE category (
 category_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 name VARCHAR(120) NOT NULL UNIQUE CHECK (TRIM(name)<>'')
) ENGINE=InnoDB;
CREATE TABLE subcategory (
 subcategory_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 category_id BIGINT NOT NULL,
 name VARCHAR(120) NOT NULL,
 UNIQUE(category_id,name),
 FOREIGN KEY(category_id) REFERENCES category(category_id) ON DELETE RESTRICT
) ENGINE=InnoDB;
CREATE TABLE manufacturer (
 manufacturer_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 name VARCHAR(120) NOT NULL UNIQUE
) ENGINE=InnoDB;
CREATE TABLE size (
 size_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 label VARCHAR(30) NOT NULL UNIQUE
) ENGINE=InnoDB;
-- === Товар и сочетание модели с размером
CREATE TABLE product (
 product_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 subcategory_id BIGINT NOT NULL,
 manufacturer_id BIGINT NOT NULL,
 name VARCHAR(200) NOT NULL,
 image_path VARCHAR(255) NOT NULL DEFAULT '',
 description TEXT NOT NULL,
 composition TEXT NOT NULL,
 price DECIMAL(12,2) NOT NULL CHECK(price>0),
 UNIQUE(name,manufacturer_id),
 FOREIGN KEY(subcategory_id) REFERENCES subcategory(subcategory_id) ON DELETE RESTRICT,
 FOREIGN KEY(manufacturer_id) REFERENCES manufacturer(manufacturer_id) ON DELETE RESTRICT
) ENGINE=InnoDB;
CREATE TABLE stock_item (
 item_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 product_id BIGINT NOT NULL,
 size_id BIGINT NOT NULL,
 available INT NOT NULL CHECK(available>=0),
 UNIQUE(product_id,size_id),
 FOREIGN KEY(product_id) REFERENCES product(product_id) ON DELETE RESTRICT,
 FOREIGN KEY(size_id) REFERENCES size(size_id) ON DELETE RESTRICT
) ENGINE=InnoDB;
-- === Клиент, заголовок заказа и исторические строки
CREATE TABLE app_role (
 role_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;
CREATE TABLE customer (
 customer_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 login VARCHAR(80) NOT NULL UNIQUE,
 last_name VARCHAR(80) NOT NULL,
 first_name VARCHAR(80) NOT NULL,
 patronymic VARCHAR(80) NOT NULL DEFAULT '',
 role_id BIGINT NOT NULL,
 FOREIGN KEY(role_id) REFERENCES app_role(role_id) ON DELETE RESTRICT
) ENGINE=InnoDB;
CREATE TABLE sales_order (
 order_id BIGINT PRIMARY KEY AUTO_INCREMENT,
 customer_id BIGINT NOT NULL,
 ordered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(customer_id) REFERENCES customer(customer_id) ON DELETE RESTRICT
) ENGINE=InnoDB;
CREATE TABLE order_line (
 order_id BIGINT NOT NULL,
 item_id BIGINT NOT NULL,
 quantity INT NOT NULL CHECK(quantity>0),
 unit_price DECIMAL(12,2) NOT NULL CHECK(unit_price>0),
 PRIMARY KEY(order_id,item_id),
 FOREIGN KEY(order_id) REFERENCES sales_order(order_id) ON DELETE CASCADE,
 FOREIGN KEY(item_id) REFERENCES stock_item(item_id) ON DELETE RESTRICT
) ENGINE=InnoDB;
