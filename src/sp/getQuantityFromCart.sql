/* Stored procedure for query:
 * SELECT quantity FROM shopping_cart WHERE item_id = %s and username = %s */
 
DROP PROCEDURE IF EXISTS getQuantityFromCart;

DELIMITER //

CREATE PROCEDURE getQuantityFromCart( IN username varchar(50),
                                      IN id int(11),
                                      OUT q int(11) )
                                  
BEGIN
    SELECT quantity
    INTO q
    FROM shopping_cart s
    WHERE s.item_id = id and s.username = username;

END //
DELIMITER ;