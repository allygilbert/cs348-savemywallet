/* Stored procedure for query:
 * SELECT * FROM payment WHERE username = %s */
 
DROP PROCEDURE IF EXISTS getPaymentFromUsername;

DELIMITER //

CREATE PROCEDURE getPaymentFromUsername( IN username varchar(50) )
                                  
BEGIN
    SELECT *
    FROM payment
    WHERE payment.username = username;

END //
DELIMITER ;