import mysql.connector
from mysql.connector import Error
import connection_info

id = 0

def addUser():
    cnx = mysql.connector.connect(user=connection_info.MyUser, password=connection_info.MyPassword,
                                    host=connection_info.MyHost,
                                    database=connection_info.MyDatabase)
    cursor = cnx.cursor()

f =open('index.html', 'r')
#TODO: Extract values from name and monthlybudget and automatically increment id
id = id + 1
name = "jean" #extract name
monthly_budget = "2"
    query = ("INSERT INTO user VALUES (%s,%s, %s)")
    cursor.execute(query, str(id), name, monthly_budget)

    cnx.commit()

    f.close()
    cursor.close()
    cnx.close()    ~~