/* Stored procedure for query:
 * SELECT i.name, i.price, s.quantity FROM shopping_cart s JOIN item i ON s.item_id = i.item_id WHERE s.username = %s */
 
DROP PROCEDURE IF EXISTS getCartFromUsername;

DELIMITER //

CREATE PROCEDURE getCartFromUsername( IN username varchar(50) )
                                  
BEGIN
    SELECT i.name, i.price, s.quantity
    FROM shopping_cart s JOIN item i ON s.item_id = i.item_id
    WHERE s.username = username;

END //
DELIMITER ;