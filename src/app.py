from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import connection_info

app = Flask(__name__)

cnx = mysql.connector.connect(user=connection_info.MyUser, password=connection_info.MyPassword, host=connection_info.MyHost, database=connection_info.MyDatabase, port='3306')

@app.route('/')
def hello():
    return 'Hello, world!'

# a simple page that says hello
@app.route('/index', methods = ['GET', 'POST'])
def index():
    msg = ''
    if 'username' in request.form and 'monthlybudget' in request.form:
        username = request.form['username']
        budget = request.form['monthlybudget']
        cursor = cnx.cursor(buffered = True)
        query = "SELECT * FROM user WHERE username = %s"
        cursor.execute(query, (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Log in successful.'
            return render_template('index.html', msg = msg)

# registers a new user and inserts data into database
@app.route('/register', methods = ['GET', 'POST'])
def register():
    global indx
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'monthlybudget' in request.form:
        username = request.form['username']
        budget = request.form['monthlybudget']

        print(username)
        print(budget)

        cursor = cnx.cursor(buffered = True)
        query = "SELECT * FROM user WHERE username = %s"
        cursor.execute(query, (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Username already exists.'
        else:
            insertcursor = cnx.cursor(buffered = True)
            query = "INSERT INTO user VALUES (%s, %s)"
            insertcursor.execute(query, (username, budget,))
            cnx.commit()
            msg = 'New account successfully registered.'
    
    elif request.method == 'POST':
        msg = 'Please fill in the empty fields.'
    
    return render_template('register.html', msg = msg)
    

if __name__ == "__main__":
    app.debug = True
    app.run()
