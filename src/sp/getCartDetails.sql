/* Stored procedure for query:
 * SELECT item_id, quantity FROM shopping_cart WHERE username = %s */
 
DROP PROCEDURE IF EXISTS getCartDetails;

DELIMITER //

CREATE PROCEDURE getCartDetails( IN username varchar(50) )
                                  
BEGIN
    SELECT item_id, quantity
    FROM shopping_cart s
    WHERE s.username = username;

END //
DELIMITER ;