from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import connection_info

app = Flask(__name__)
app.secret_key = 'IUSUCKS'

cnx = mysql.connector.connect(user=connection_info.MyUser, password=connection_info.MyPassword, host=connection_info.MyHost, database=connection_info.MyDatabase, port='3306')

@app.route('/')
@app.route('/login', methods = ['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'monthlybudget' in request.form:
        username = request.form['username']
        budget = request.form['monthlybudget']
        
        cursor = cnx.cursor(buffered = True)
        query = "SELECT username, monthly_budget FROM user WHERE username = %s and monthly_budget = %s"
        cursor.execute(query, (username, budget,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['username'] = account[0]
            msg = "Log in successful!"
            return redirect(url_for('delete')) # TODO: change to home page
        else:
            msg = 'Incorrect username or monthly budget.'

    elif request.method == 'POST':
        msg = 'Please fill in the empty fields.'

    return render_template('login.html', msg = msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# deletes a user account and removes data from database
@app.route('/deleteaccount', methods = ['GET', 'POST'])
def delete():
    msg = ''
    if 'loggedin' in session:
        if request.method == 'POST' and 'username' in request.form and 'monthlybudget' in request.form:
            username = request.form['username']
            budget = request.form['monthlybudget']
            
            cursor = cnx.cursor(buffered = True)
            query = "SELECT username, monthly_budget FROM user WHERE username = %s"
            cursor.execute(query, (username,))
            account = cursor.fetchone()
            if account:
                # confirm monthly budget
                if float(budget) == float(account[1]):
                    deletecursor = cnx.cursor(buffered = True)
                    query = "DELETE FROM user WHERE username = %s and monthly_budget = %s"
                    deletecursor.execute(query, (username, budget,))
                    cnx.commit()
                    msg = 'Account successfully deleted.'
                    return redirect(url_for('login'))
                else:
                    msg = 'Incorrect monthly budget.'
            else:
                msg = 'Username does not exist.'
        
        elif request.method == 'POST':
            msg = 'Please fill in the empty fields.'
        
        return render_template('delete.html', msg = msg)

    else:
        return redirect(url_for('login'))

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

@app.route('/paymentmethod', methods = ['GET', 'POST'])
def paymentmethod():
    msg = ''
    if 'loggedin' in session:
        if request.method == 'POST' and 'cardNumber' in request.form and 'cardholderName' in request.form and 'expirationDate' in request.form:
            username = session['username'];
            cardNumber = request.form['cardNumber']
            cardholderName = request.form['cardholderName']
            expirationDate = request.form['expirationDate']

            cursor = cnx.cursor(buffered = True)
            query = "SELECT * FROM payment WHERE username = %s"
            cursor.execute(query, (username,))
            account = cursor.fetchone()
            if account:
                # TODO: account can only have one payment method ???
                msg = 'Payment method already exists for this account.'
                
            else:
                # insert account payment method
                insertcursor = cnx.cursor(buffered = True)
                query = "INSERT INTO payment VALUES (%s, %s, %s, %s)"
                insertcursor.execute(query, (cardNumber, username, cardholderName, expirationDate,))
                cnx.commit()
                msg = 'Payment method successfully saved.'

        elif request.method == 'POST':
            msg = 'Please fill in the empty fields.'

        return render_template('payment.html', msg = msg)

    else:
        return redirect(url_for('login'))

@app.route('/purchase', methods = ['GET', 'POST'])
def purchase():
    msg = ''
    if 'loggedin' in session:
        if request.method == 'GET':  # generate purchase.html
            # set up html file
            htmlprologue = '''<html lang="en">
                            <head>
                                <title> purchase </title>
                                <link rel="stylesheet" href="../static/style.css">
                            </head>
                            <body>
                                <div class="one">
                                    <div class="sidebar">
                                        <h1>Menu</h1>
                                        <ul>
                                            <li><a href="{{url_for('paymentmethod')}}">Payment Method</a></li>
                                            <li class="active"><a href="{{url_for('purchase')}}">Purchase Cart</a></li>
                                            <li><a href="{{url_for('delete')}}">Delete Account</a></li>
                                            <li><a href="{{url_for('logout')}}">Logout</a></li>
                                        </ul> 
                                    </div>
                                    <div class="content" align="center">
                                        <div class="header">
                                            <h1>Purchase Cart</h1>
                                        </div></br></br>
                                        <div class="contentbar">
                                            <form action="{{ url_for('purchase')}}" method="post" autocomplete="off">
                                            <div class="msg">{{ msg }}</div>
                                            <h1>Cart Contents</h1></br>'''
            htmlmiddle = '''<h1>Payment Method</h1></br>'''
            htmlepilogue = '''<input type="submit" class="btn" name="purchase" value="Place Order">
                            </div>
                        </div>
                    </div>
                </body>
            </html>'''

            # create html table for cart info
            carttable = "<table><tr class='worddark'><td>Item</td><td>Price</td><td>Quantity</td></tr>"
            cartcursor = cnx.cursor(buffered = True)
            cartquery = "SELECT i.name, i.price, s.quantity FROM shopping_cart s JOIN item i ON s.item_id = i.item_id WHERE s.username = %s"
            cartcursor.execute(cartquery, (session['username'],))

            for (item, price, quantity) in cartcursor:
                carttable += "<tr><td>%s</td>"  % item
                carttable += "<td>%s</td>"      % price
                carttable += "<td>%s</td></tr>" % quantity

            carttable += "</table></br>"

            # create html for payment info
            paymentcursor = cnx.cursor(buffered = True)
            paymentquery = "SELECT * FROM payment WHERE username = %s"
            paymentcursor.execute(paymentquery, (session['username'],))
            payment = paymentcursor.fetchone()
            
            paymentinfo = '''<table>
                                <tr>
                                    <td class='worddark'>Card Number</td>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <td class='worddark'>Name on Card</td>
                                    <td>%s</td>
                                </tr>
                                <tr>
                                    <td class='worddark'>Expiration Date</td>
                                    <td>%s</td>
                                </tr>
                            </table></br>''' % (payment[0], payment[1], payment[2])

            # write html file
            f = open("templates/purchase.html", "w")
            f.write(htmlprologue)
            f.write(carttable)
            f.write(htmlmiddle)
            f.write(paymentinfo)
            f.write(htmlepilogue)
            f.close()

            return render_template("purchase.html")

        elif request.method == 'POST':
            transactionID = createNewTransaction()  # create new transaction entry
            transferCart(transactionID)  # move items in user's cart to transaction-item relation
            storePurchase(transactionID)  # store user's payment info with a purchase
            clearCart()  # clear user's shopping cart

            msg = 'Order successfully placed!'
            return render_template("purchase.html", msg = msg)

    else:
        return redirect(url_for('login'))

def clearCart():
    cursor = cnx.cursor(buffered = True)
    query = "DELETE FROM shopping_cart WHERE username = %s"
    cursor.execute(query, (session['username'],))
    cnx.commit()
    cursor.close()

def createNewTransaction():
    # get next transaction ID number
    cursor = cnx.cursor(buffered = True)
    query = "SELECT transaction_id FROM transaction ORDER BY transaction_id DESC"
    cursor.execute(query)
    latestTransaction = cursor.fetchone()

    transactionID = -1
    if latestTransaction:
        print(latestTransaction[0])
        transactionID = latestTransaction[0] + 1
        print(transactionID)
    else:
        transactionID = 0

    # compute transaction total by totaling cart
    totalquery = "SELECT sum(i.price * s.quantity) FROM shopping_cart s JOIN item i ON s.item_id = i.item_id WHERE s.username = %s"
    cursor.execute(totalquery, (session['username'],))
    cart = cursor.fetchone()
    total = cart[0]

    # insert new entry into table
    cursor = cnx.cursor(buffered = True)
    insertquery = "INSERT INTO transaction VALUES(%s, %s)"
    cursor.execute(insertquery, (transactionID, total, ))
    cnx.commit()

    cursor.close()
    return transactionID

def storePurchase(transactionID):
    cursor = cnx.cursor(buffered = True)

    # get payment info
    paymentquery = "SELECT payment_id FROM payment WHERE username = %s"
    cursor.execute(paymentquery, (session['username'],))
    payment = cursor.fetchone()
    paymentID = payment[0]

    insertquery = "INSERT INTO purchase VALUES(%s, %s, %s, %s)"
    cursor.execute(insertquery, (session['username'], transactionID, paymentID, datetime.now().strftime("%m/%d/%Y"),))
    cursor.close()

def transferCart(transactionID):
    # get cart items
    cursor = cnx.cursor(buffered = True)
    cartquery = "SELECT item_id, quantity FROM shopping_cart WHERE username = %s"
    cursor.execute(cartquery, (session['username'],))

    count = 0
    insertquery = "INSERT INTO item_transaction VALUES "
    for (item, quantity) in cursor:
        if count == 0:
            insertquery += "(%s, %s, %s)" % (item, transactionID, quantity)
            count += 1
        else:
            insertquery += ", (%s, %s, %s)" % (item, transactionID, quantity)

    # insert items into item_transaction relation
    cursor.execute(insertquery)

    cursor.close()

# registers a new user and inserts data into database
@app.route('/register', methods = ['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'monthlybudget' in request.form:
        username = request.form['username']
        budget = request.form['monthlybudget']

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
