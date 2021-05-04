import mysql.connector
from mysql.connector import Error
import connection_info


def addUser(user_id, name, monthly_budget):
    
    cnx = mysql.connector.connect(user=connection_info.MyUser, password=connection_info.MyPassword,
                                    host=connection_info.MyHost,
                                    database=connection_info.MyDatabase)
    cursor = cnx.cursor()

    f =open('../flaskr/templates/index.html', 'r')
    #TODO: Extract values from name and monthlybudget and automatically increment id
    #id = id + 1
    name = name #extract name
    monthly_budget = monthly_budget
    user_id = user_id
    query = ("INSERT INTO user VALUES (%s,%s, %s)")
    cursor.execute(query, (user_id, name, monthly_budget))
    
    cnx.commit()

    f.close()
    cursor.close()
    cnx.close()    