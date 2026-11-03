# Словарь полей демонстрационной модели

PK — первичный ключ; FK — внешний ключ. Полные типы и ограничения находятся в 01_schema.sql. Для своей схемы сохранить этот документ с уточнениями предметной области.

## category — Категория
category_id — PK; name — уникальное непустое название.

## subcategory — Подкатегория
subcategory_id — PK; category_id — FK category; name — название. Пара category_id,name уникальна.

## manufacturer — Производитель
manufacturer_id — PK; name — уникальное название.

## size — Маркировка
size_id — PK; label — уникальная строковая маркировка, включая буквенные размеры.

## product — Модель
product_id — PK; subcategory_id и manufacturer_id — FK. name — модель; image_path — относительный путь; description — описание; composition — состав; price — текущая положительная цена DECIMAL(12,2). Пара name,manufacturer_id уникальна.

## stock_item — Размерная позиция
item_id — PK; product_id и size_id — FK; available — целый неотрицательный остаток. Пара product_id,size_id уникальна.

## app_role — Роль клиента в исходной системе
role_id — PK; name — уникальное название роли. Не является серверной учётной записью СУБД.

## customer — Клиент
customer_id — PK; login — уникальный логин; last_name,first_name — фамилия и имя; patronymic — отчество или пустая строка; role_id — FK app_role. В исходниках нет пароля клиента.

## sales_order — Исторический заказ
order_id — PK, номер из источника; customer_id — FK; ordered_at — дата и время заказа. Общая сумма вычисляется из строк.

## order_line — Историческая строка
order_id и item_id образуют составной PK и являются FK. quantity — положительное целое; unit_price — положительная цена покупки DECIMAL(12,2), независимая от текущей product.price.

## Промежуточный слой и журнал
Пять stg_таблиц повторяют поля CSV как TEXT до проверки. source_file — имя источника; source_row — номер исходной записи с учётом заголовка, начинается с 2. import_issue хранит source_file, source_row, issue_code, reason, disposition, old_value, new_value. Одна строка может иметь несколько разных причин; число отклонённых записей считают по различным координатам.

## Правила удаления
RESTRICT сохраняет используемые справочники, модели, позиции и клиентов. CASCADE действует только от заголовка заказа к его строкам; он не возвращает остатки. Создание и удаление новых заказов не являются заданием обязательной части.
