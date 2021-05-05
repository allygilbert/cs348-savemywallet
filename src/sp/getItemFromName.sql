/* Stored procedure for query:
 * SELECT item_id FROM item WHERE name = %s */
 
DROP PROCEDURE IF EXISTS getItemFromName;

DELIMITER //

CREATE PROCEDURE getItemFromName( IN itemName varchar(50), 
                                  OUT id int(11) )
                                  
BEGIN
    SELECT item_id
    INTO id
    FROM item
    WHERE name = itemName;

END //
DELIMITER ;