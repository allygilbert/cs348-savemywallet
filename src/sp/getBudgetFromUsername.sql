/* Stored procedure for query:
 * SELECT monthly_budget FROM user WHERE username = %s */
 
DROP PROCEDURE IF EXISTS getBudgetFromUsername;

DELIMITER //

CREATE PROCEDURE getBudgetFromUsername( IN username varchar(50),
                                        OUT budget decimal(5,2) )
                                  
BEGIN
    SELECT monthly_budget
    INTO budget
    FROM user
    WHERE user.username = username;

END //
DELIMITER ;