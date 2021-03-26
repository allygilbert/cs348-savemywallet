import mysql.connector
from mysql.connector import Error
import connection_info



def printUsers():
    cnx = mysql.connector.connect(user=connection_info.MyUser, password=connection_info.MyPassword,
                                    host=connection_info.MyHost,
                                    database=connection_info.MyDatabase)
    cursor = cnx.cursor()

    query = ("SELECT * from user")

    cursor.execute(query)


    table = "<html><h1> Existing users </h1><table border = '1'>"

    for (user_id, username, monthly_budget) in cursor:
        table = table + "<tr>\n"
        table = table + "<td>" + str(user_id) + "</td>"
        table = table + "<td>" + username + "</td>"
        table = table + "<td>" + str(monthly_budget) + "</td>"
        table = table + "</tr>\n"

    table = table + "</table> </html>"

    f = open("./templates/results.html", "w")

    f.write(table)

    f.close()
    cursor.close()
    cnx.close()    