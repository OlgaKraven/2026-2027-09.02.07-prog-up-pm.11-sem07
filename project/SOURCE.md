# Происхождение материалов

Исходное описание торговой организации, импортные таблицы и изображения предоставлены преподавателем. Excel преобразован в CSV UTF-8 с английскими заголовками, датами YYYY-MM-DD HH:MM:SS и десятичной точкой; содержательные данные сохранены. Исправление двух обнаруженных расхождений названий показано отдельно в SQL и методичке.

Демонстрационная схема, SQL и индивидуальные дополнительные задания разработаны для этого комплекта. Роли СУБД, процедура заказа, конкурентные покупки, индексы и резервное копирование сохранены в отдельном разделе для углубления. Они не являются обязательным условием приёмки схемы и импорта. Индивидуальные CSV являются учебными синтетическими данными.

Оригинальные XLSX сохранены в data/original. Карта полей, преобразований и контрольных чисел находится в INPUT_MAPPING.md. В шести текстовых ячейках Products_import.xlsx при подготовке CSV удалены внешние пробелы или переносы; исходные XLSX не изменялись. Полную сверку значений выполняет tools/convert_sources.py. Исправления промежуточного слоя имеют координаты и старое/новое значение в import_issue.

Справка по обработчикам и RESIGNAL: https://mariadb.com/docs/server/reference/sql-statements/programmatic-compound-statements/declare-handler
Справка по JSON_EXTRACT: https://mariadb.com/docs/server/reference/sql-functions/special-functions/json-functions/json_extract
Справка по ролям: https://mariadb.com/docs/server/security/user-account-management/roles/roles_overview
Справка по SET DEFAULT ROLE: https://mariadb.com/docs/server/reference/sql-statements/account-management-sql-statements/set-default-role
