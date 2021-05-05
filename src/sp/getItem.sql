/* Stored procedure for query:
 * SELECT name, price FROM item */
 
DROP PROCEDURE IF EXISTS getItem;

DELIMITER //

CREATE PROCEDURE getItem()
                                  
BEGIN
    SELECT name, price
    FROM item;

END //
DELIMITER ;