/* Stored procedure for query:
 * UPDATE shopping_cart SET quantity=%s WHERE item_id = %s AND username = %s */
 
DROP PROCEDURE IF EXISTS updateCartQuantity;

DELIMITER //

CREATE PROCEDURE updateCartQuantity( IN username varchar(50),
                                     IN id int(11),
                                     IN q int(11) )
                                  
BEGIN
    UPDATE shopping_cart
    SET quantity = q
    WHERE item_id = id AND shopping_cart.username = username;

END //
DELIMITER ;