-- === Объявление процедуры, курсора и обработчиков
SET SESSION sql_mode='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
DELIMITER $$
CREATE PROCEDURE place_order(IN p_customer BIGINT,IN p_lines LONGTEXT)
SQL SECURITY DEFINER
BEGIN
 DECLARE v_order BIGINT;
 DECLARE v_item BIGINT;
 DECLARE v_quantity INT;
 DECLARE v_available INT;
 DECLARE v_price DECIMAL(12,2);
 DECLARE v_index INT DEFAULT 0;
 DECLARE v_count INT;
 DECLARE v_done INT DEFAULT 0;
 DECLARE v_id_text TEXT;
 DECLARE v_qty_text TEXT;
 DECLARE cur CURSOR FOR SELECT item_id,quantity FROM request_lines ORDER BY item_id;
 DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done=1;
 DECLARE EXIT HANDLER FOR SQLEXCEPTION
 BEGIN
  ROLLBACK;
  DROP TEMPORARY TABLE IF EXISTS request_lines;
  RESIGNAL;
 END;
 -- === Подготовка и проверка списка заказа
 IF p_lines IS NULL OR JSON_VALID(p_lines)=0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid JSON';
 END IF;
 IF JSON_TYPE(p_lines)<>'ARRAY' OR JSON_LENGTH(p_lines)=0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Nonempty array required';
 END IF;
 DROP TEMPORARY TABLE IF EXISTS request_lines;
 CREATE TEMPORARY TABLE request_lines (
  item_id BIGINT PRIMARY KEY,quantity INT NOT NULL
 ) ENGINE=InnoDB;
 SET v_count=JSON_LENGTH(p_lines);
 WHILE v_index<v_count DO
  SET v_id_text=JSON_UNQUOTE(JSON_EXTRACT(p_lines,CONCAT('$[',v_index,'].item_id')));
  SET v_qty_text=JSON_UNQUOTE(JSON_EXTRACT(p_lines,CONCAT('$[',v_index,'].quantity')));
  IF v_id_text IS NULL OR v_qty_text IS NULL
   OR v_id_text NOT REGEXP '^[1-9][0-9]*$'
   OR v_qty_text NOT REGEXP '^[1-9][0-9]*$' THEN
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Positive integer item and quantity required';
  END IF;
  INSERT INTO request_lines VALUES(CAST(v_id_text AS UNSIGNED),CAST(v_qty_text AS UNSIGNED))
  ON DUPLICATE KEY UPDATE quantity=quantity+VALUES(quantity);
  SET v_index=v_index+1;
 END WHILE;
 -- === Транзакция и блокировка товарных позиций
 START TRANSACTION;
 INSERT INTO sales_order(customer_id) VALUES(p_customer);
 SET v_order=LAST_INSERT_ID();
 OPEN cur;
 read_loop: LOOP
  FETCH cur INTO v_item,v_quantity;
  IF v_done=1 THEN LEAVE read_loop; END IF;
  SET v_available=NULL;
  SELECT s.available,p.price INTO v_available,v_price
  FROM stock_item s JOIN product p USING(product_id)
  WHERE s.item_id=v_item FOR UPDATE;
  IF v_available IS NULL THEN
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unknown item';
  END IF;
  IF v_available<v_quantity THEN
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Not enough stock';
  END IF;
  -- === Историческая цена, остаток и атомарное завершение
  INSERT INTO order_line(order_id,item_id,quantity,unit_price)
  VALUES(v_order,v_item,v_quantity,v_price);
  UPDATE stock_item SET available=available-v_quantity WHERE item_id=v_item;
 END LOOP;
 CLOSE cur;
 COMMIT;
 DROP TEMPORARY TABLE request_lines;
 SELECT v_order AS created_order;
END$$
DELIMITER ;
