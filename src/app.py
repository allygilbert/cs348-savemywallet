from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import connection_info

app = Flask(__name__)
app.secret_key = 'IUSUCKS'
app.config.update(
    TEMPLATES_AUTO_RELOAD=True
)

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
        cursor.close()
        if account:
            session['loggedin'] = True
            session['username'] = account[0]
            msg = "Log in successful!"
            return redirect(url_for('shop'))
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
            cursor.close()
            if account:
                # confirm monthly budget
                if float(budget) == float(account[1]):
                    deletecursor = cnx.cursor(buffered = True)
                    query = "DELETE FROM user WHERE username = %s and monthly_budget = %s"
                    deletecursor.execute(query, (username, budget,))
                    cnx.commit()
                    msg = 'Account successfully deleted.'
                    deletecursor.close()
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
        cursor.close()
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
            cursor.close()
            if account:
                # TODO: account can only have one payment method ???
                msg = 'Payment method already exists for this account.'
                
            else:
                # insert account payment method
                insertcursor = cnx.cursor(buffered = True)
                query = "INSERT INTO payment VALUES (%s, %s, %s, %s)"
                insertcursor.execute(query, (cardNumber, username, cardholderName, expirationDate,))
                cnx.commit()
                insertcursor.close()
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
                                            <li><a href="{{url_for('shop')}}">Shop</a></li>
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
            
          #  cartSnippet = cartcursor.fetchone
            
            for (item, price, quantity) in cartcursor:
                carttable += "<tr><td>%s</td>"  % item
                carttable += "<td>%s</td>"      % price
                carttable += "<td>%s</td>" % quantity
                carttable += '''<td> <form action="{{ url_for('purchase')}}" method="post" autocomplete="off">                   <input type="hidden" name="item_name" value="%s">''' % item
       
                carttable += '''<input type="submit" class="btn" value="Remove" name="Remove"><input type="number" name="new_quantity" placeholder="10"><input type="submit" class="btn" value="Change Quantity" name="Change Quantity"></form></td></tr>'''


            cartcursor.close()
            carttable += "</table></br>"

            # create html for payment info
            paymentcursor = cnx.cursor(buffered = True)
            paymentquery = "SELECT * FROM payment WHERE username = %s"
            paymentcursor.execute(paymentquery, (session['username'],))
            payment = paymentcursor.fetchone()
            paymentcursor.close()
            
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

        if request.method == 'POST':
            username = session['username']
            print(request.form)
            if 'Remove' in request.form:
                cursor = cnx.cursor(buffered = True)
                print("REMOVE")
                print("after username")
                print(request.form)
                name = request.form['item_name']
                print(name)   
                findItemId = "SELECT item_id FROM item WHERE name = %s"
                cursor.execute(findItemId, (name,))
                item_id = cursor.fetchone()
                print("item_id:")
                print(item_id[0])
                #find quantity
                find_quantity = "SELECT quantity FROM shopping_cart WHERE username = %s and item_id = %s"
                cursor.execute(find_quantity, (session['username'], item_id[0],))

                quantity = cursor.fetchone()
                quantity = quantity[0]
                if(quantity == 1):
                    print("about to delete item")
                    deleteItem = 'DELETE FROM shopping_cart WHERE item_id = %s AND username=%s'
                    cursor.execute(deleteItem, (item_id[0], username,))
                    cursor.close()
                    cnx.commit()
                    showCart()
                else: 
                    newQuantity = quantity - 1
                    updateQuantity = "UPDATE shopping_cart SET quantity=%s WHERE item_id = %s AND username = %s"
                    cursor.execute(updateQuantity, (newQuantity, item_id[0], username, ))
                    cursor.close()
                    cnx.commit()
                    showCart()
              
            if 'Change Quantity' in request.form:
                cursor = cnx.cursor(buffered = True)
                new_quantity = request.form['new_quantity']
                name = request.form['item_name']
                print(name)   
                findItemId = "SELECT item_id FROM item WHERE name = %s"
                cursor.execute(findItemId, (name,))
                item_id = cursor.fetchone()
                print("item_id:")
                print(item_id[0])
                print("CHANGE QUANTITY")
                getQuantity = "SELECT quantity FROM shopping_cart WHERE item_id = %s AND username = %s"
                cursor.execute(getQuantity, (item_id[0], username,))
                quantity = cursor.fetchone()
                print(quantity[0])
                updateQuantity = "UPDATE shopping_cart SET quantity=%s WHERE item_id = %s AND username = %s"
                cursor.execute(updateQuantity, (new_quantity, item_id[0], username, ))
                cursor.close()
                cnx.commit()
                showCart()
        if 'purchase' in request.form:
            print("createNewTransaction")
            transactionID = createNewTransaction()  # create new transaction entry
            transferCart(transactionID)  # move items in user's cart to transaction-item relation
            storePurchase(transactionID)  # store user's payment info with a purchase
            clearCart()  # clear user's shopping cart
            showCart()

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
def showCart():
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
                    <li><a href="{{url_for('shop')}}">Shop</a></li>
                <li><a href="{{url_for('paymentmethod')}}">Payment Method</a></li>
                <li><a href="{{url_for('budget')}}">Budget</a></li>
                <li><a href="{{url_for('purchase')}}">Purchase Cart</a></li>
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
    cartcursor = cnx.cursor(buffered=True)
    cartquery = "SELECT i.name, i.price, s.quantity FROM shopping_cart s JOIN item i ON s.item_id = i.item_id WHERE s.username = %s"
    cartcursor.execute(cartquery, (session['username'],))

    #  cartSnippet = cartcursor.fetchone

    for (item, price, quantity) in cartcursor:
        carttable += "<tr><td>%s</td>" % item
        carttable += "<td>%s</td>" % price
        carttable += "<td>%s</td>" % quantity
        carttable += '''<td> <form action="{{ url_for('purchase')}}" method="post" autocomplete="off">                   <input type="hidden" name="item_name" value="%s">''' % item
        carttable += '''<input type="submit" class="btn" value="Remove" name="Remove"><input type="number" name="new_quantity" placeholder="10"><input type="submit" class="btn" value="Change Quantity" name="Change Quantity"></form></td></tr>'''

    cartcursor.close()
    carttable += "</table></br>"
    # create html for payment info
    paymentcursor = cnx.cursor(buffered = True)
    paymentquery = "SELECT * FROM payment WHERE username = %s"
    paymentcursor.execute(paymentquery, (session['username'],))
    payment = paymentcursor.fetchone()
    paymentcursor.close()
    
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
    print("cart total")
    print(total)

    # insert new entry into table
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
        cursor.close()
        if account:
            msg = 'Username already exists.'
        else:
            insertcursor = cnx.cursor(buffered = True)
            query = "INSERT INTO user VALUES (%s, %s)"
            insertcursor.execute(query, (username, budget,))
            cnx.commit()
            insertcursor.close()
            msg = 'New account successfully registered.'
    
    elif request.method == 'POST':
        msg = 'Please fill in the empty fields.'
    
    return render_template('register.html', msg = msg)


@app.route('/shop', methods = ['GET', 'POST'])
def shop():
    print("in shop")
    if request.method == 'POST':
        print("post:")
        cursor = cnx.cursor(buffered = True)
        print("after cursor")
        username = session['username']
        print("after requesting username")

        name = request.form['item_name']
        print("after requesting item_name")

        quantity = request.form['quantity']
        print("after requesting quantity")

        print("after requesting form elements")
        findPrice = "SELECT price FROM item WHERE name = %s"
        cursor.execute(findPrice, (name,))
        print("after first query execution")

        price = cursor.fetchone()
        print("name:")
        print(name)
        print(quantity)
        print(findPrice)
        print("Adding item to cart")
        findItemId = "SELECT item_id FROM item WHERE item.name = %s"
        cursor.execute(findItemId, (name,))
        item_id = cursor.fetchone()
        print("item_id:")
        print(item_id[0])
       # print(username)
        findItem = "SELECT item_id FROM shopping_cart where username= %s AND item_id = %s"
        cursor.execute(findItem, (username, item_id[0]))
        it = cursor.fetchone()
        print("it: ")
        print(it)

    
        if( it is None ):
            print("item isnt in shopping cart") 
            addToShoppingCart = "INSERT INTO shopping_cart VALUES(%s,%s,%s)"
            cursor.execute(addToShoppingCart, (item_id[0], username, quantity,))
        else:
            print("item is in shopping cart") 

            item = cursor.fetchone()
            getQuantity = "SELECT quantity FROM shopping_cart WHERE item_id = %s AND username = %s"
            cursor.execute(getQuantity, (item_id[0], username,))
            quantity = cursor.fetchone()
            print(quantity[0])
            updateQuantity = "UPDATE shopping_cart SET quantity=%s WHERE item_id = %s AND username = %s"
            cursor.execute(updateQuantity, (quantity[0]+1, item_id[0], username, ))
            
       
       # addToShoppingCart = "INSERT INTO shopping_cart VALUES(%s,%s,%s)"
        #cursor.execute(addToShoppingCart, (item_id[0], username, quantity,))
        #cursor = cnx.cursor(buffered = True)
    return render_template('shop.html')

@app.route('/shopping_cart', methods = ['GET', 'POST'])
def shopping_cart():    
    print("IN SHOPPING CART WOHOO")
    hello = "<h1> WHASSUPPPPPP </h1>"
    f = open("shopping_cart.html", "w")
    f.write(hello)

    username = session['username']
    if request.method == 'POST':
        cursor = cnx.cursor(buffered = True)
        findItemId = "SELECT item_id FROM item WHERE item.name = %s"
        cursor.execute(findItemId, (name,))
        item_id = cursor.fetchone()
        #print(request.form.get("Remove"))
        if 'Remove' in request.form:
            print("REMOVE")
            print("after username")
            print(request.form)
            name = request.form['item_name']    
            print("item_id:")
            print(item_id[0])
            
          #  deleteItem = 'DELETE FROM shopping_cart WHERE item_id = %s AND username=%s'
           # cursor.execute(deleteItem, (item_id[0], username,))
        elif 'Change Quantity' in request.form:
            print("CHANGE QUANTITY")
            getQuantity = "SELECT quantity FROM shopping_cart WHERE item_id = %s AND username = %s"
            cursor.execute(getQuantity, (item_id[0], username,))
            quantity = cursor.fetchone()
            print(quantity[0])
            updateQuantity = "UPDATE shopping_cart SET quantity=%s WHERE item_id = %s AND username = %s"
            cursor.execute(updateQuantity, (quantity[0]+1, item_id[0], username, ))
        
        cursor = cnx.cursor(buffered = True)
        findBudget = "SELECT monthly_budget FROM user WHERE username= %s"
        cursor.execute(findBudget, (username,))
        budget = cursor.fetchone()
        print(budget[0])
        findItemsIds = "SELECT item_id FROM shopping_cart WHERE username= %s"
        itemsIds = cursor.fetchall();
    return render_template('shopping_cart.html')

def cart_total():
    #find all items
    total = 0
    cursor = cnx.cursor(buffered=True)
    find_id_and_quantity = "SELECT item_id, quantity FROM shopping_cart WHERE username = %s"
    cursor.execute(find_id_and_quantity, (session['username'],))

    for (item_id, quantity) in cursor:
        #for all items, add price * quantity to total
        find_price = "SELECT price FROM item WHERE item_id = %s"
        cursor.execute(find_price, (item_id,) )
        price = cursor.fetchone()[0]
        total += price * quantity   
    print(total)
    return total
def compute_remaining_budget(cart_total):
    #find budget
    cursor = cnx.cursor(buffered=True)
    find_budget = "SELECT monthly_budget FROM user WHERE username = %s"
    cursor.execute(find_budget, (session['username'],))
    budget = cursor.fetchone()[0]
    print(budget)
    remaining_budget = budget - cart_total
    print(remaining_budget)
    return remaining_budget

@app.route('/budget', methods = ['GET', 'POST'])
def budget(): 
    remaining_budget = 0
    if request.method == 'GET':
        c_total = cart_total()
        print(c_total)
        remaining_budget = compute_remaining_budget(c_total)
    if request.method == 'POST':
        print(request.form)
        if 'change_budget' in request.form:
            username = session['username']
            budget = request.form['monthly_budget']
            print(username)
            print(budget)
            cursor = cnx.cursor(buffered = True)
            changeBudget = "UPDATE user SET monthly_budget = %s WHERE username = %s"
            cursor.execute(changeBudget, (budget, username,))
            cnx.commit()
            cursor.close()
        if 'add_to_budget' in request.form:
            username = session['username']
            print(username)
            #1. Get budget
            cursor = cnx.cursor(buffered = True)
            getBudget = "SELECT monthly_budget FROM user WHERE username = %s"
            cursor.execute(getBudget, (username,))
            budget = cursor.fetchone()
            budget = budget[0]
            print(budget) 
            add_to_budget = request.form['add_to_budget_i']
    
            changeBudget = "UPDATE user SET monthly_budget = %s WHERE username = %s"
            newBudget = budget + int(add_to_budget)
            cursor.execute(changeBudget, (newBudget, username,))
    return render_template('budget.html', remaining_budget = remaining_budget)

@app.route('/transaction_history', methods=['GET', 'POST'])
def transaction_history():
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
                                            <li><a href="{{url_for('shop')}}">Shop</a></li>
                                            <li><a href="{{url_for('paymentmethod')}}">Payment Method</a></li>
                                            <li class="active"><a href="{{url_for('purchase')}}">Purchase Cart</a></li>
                                            <li><a href="{{url_for('delete')}}">Delete Account</a></li>
                                            <li><a href="{{url_for('logout')}}">Logout</a></li>
                                        </ul> 
                                    </div>
                                    <div class="content" align="center">
                                       '''
    htmlepilogue = '''
                        </div>
                    </div>
                </body>
            </html>'''

    carttable = "<table><tr class='worddark'><td>username</td><td>trans_id</td><td>pay_id</td><td>date</td></tr>"
            
    cartcursor = cnx.cursor(buffered = True)
    cartquery = "SELECT username, transaction_id, payment_id, date FROM purchase WHERE username = %s"
    cartcursor.execute(cartquery, (session['username'],))
    
    #  cartSnippet = cartcursor.fetchone
    
    for (username, transaction_id, payment_id, date) in cartcursor:
        carttable += "<tr><td>%s</td>"  % username
        carttable += "<td>%s</td>"      % transaction_id
        carttable += "<td>%s</td>" % payment_id
        carttable += "<td>%s</td>" % date
    cartcursor.close()
    carttable += "</tr></table></br>"
    f = open("templates/transaction_history.html", "w")
    f.write(htmlprologue)
    f.write(carttable)
    f.write(htmlepilogue)
    f.close()
    return render_template("transaction_history.html")     

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET':
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
                        <li><a href="{{url_for('shop')}}">Shop</a></li>
                    <li><a href="{{url_for('paymentmethod')}}">Payment Method</a></li>
                    <li><a href="{{url_for('budget')}}">Budget</a></li>
                    <li><a href="{{url_for('purchase')}}">Purchase Cart</a></li>
                    <li><a href="{{url_for('delete')}}">Delete Account</a></li>
                    <li><a href="{{url_for('logout')}}">Logout</a></li>
                    </ul>
                                        </div>
                                        <div class="content" align="center">
                                            <div class="header">
                                                <h1>Purchase Cart</h1>
                                            </div></br></br>
                                            <div class="contentbar">
                                                <form action="{{ url_for('admin')}}" method="post" autocomplete="off">
                                                <div class="msg">{{ msg }}</div>
                                                <h1>Cart Contents</h1></br>'''
        htmlmiddle = '''<h1>Change item prices</h1></br>'''
        htmlepilogue = '''
                                </div>
                            </div>
                        </div>
                    </body>
                </html>'''
        # create html table for cart info
        carttable = "<table><tr class='worddark'><td>Item</td><td>Price</td><td>Edit</td></tr>"
        cartcursor = cnx.cursor(buffered=True)
        cartquery = "SELECT name, price FROM item "
        cartcursor.execute(cartquery)

        #  cartSnippet = cartcursor.fetchone

        for (item, price) in cartcursor:
            carttable += "<tr><td>%s</td>" % item
            carttable += "<td>%s</td>" % price
            carttable += '''<td> <form action="{{ url_for('admin')}}" method="post" autocomplete="off">                   <input type="hidden" name="item_name" value="%s">''' % item
            carttable += '''<input type="number" name="new_price" step="0.01" placeholder="2.99"></td><td><input type="submit" class="btn" value="Change Price" name="Change Price"></td></form></tr>'''

        cartcursor.close()
        carttable += "</table></br>"
        f = open("templates/admin.html", "w")
        f.write(htmlprologue)
        f.write(carttable)
        f.write(htmlepilogue)
        f.close()
    if request.method == 'POST':
        print(request.form)
        username = session['username']
        if "Change Price" in request.form:
            cursor = cnx.cursor(buffered=True)
            print("change price :)")
            name = request.form['item_name']
            findItemId = "SELECT item_id FROM item WHERE name = %s"
            cursor.execute(findItemId, (name,))
            item_id = cursor.fetchone()
            print("item_id:")
            print(item_id[0])
            new_price = request.form['new_price']
            #print(price)
            updatePrice = "UPDATE item SET price=%s WHERE item_id = %s "
            cursor.execute(updatePrice, (new_price, item_id[0], ))
            cursor.close()
            cnx.commit()
            showAdmin()
    return render_template("admin.html")    

def showAdmin():
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
                    <li><a href="{{url_for('shop')}}">Shop</a></li>
                <li><a href="{{url_for('paymentmethod')}}">Payment Method</a></li>
                <li><a href="{{url_for('budget')}}">Budget</a></li>
                <li><a href="{{url_for('purchase')}}">Purchase Cart</a></li>
                <li><a href="{{url_for('delete')}}">Delete Account</a></li>
                <li><a href="{{url_for('logout')}}">Logout</a></li>
                </ul>
                                    </div>
                                    <div class="content" align="center">
                                        <div class="header">
                                            <h1>Purchase Cart</h1>
                                        </div></br></br>
                                        <div class="contentbar">
                                            <form action="{{ url_for('admin')}}" method="post" autocomplete="off">
                                            <div class="msg">{{ msg }}</div>
                                            <h1>Cart Contents</h1></br>'''
    htmlmiddle = '''<h1>Change item prices</h1></br>'''
    htmlepilogue = '''
                            </div>
                        </div>
                    </div>
                </body>
            </html>'''
    # create html table for cart info
    carttable = "<table><tr class='worddark'><td>Item</td><td>Price</td><td>Edit</td></tr>"
    cartcursor = cnx.cursor(buffered=True)
    cartquery = "SELECT name, price FROM item "
    cartcursor.execute(cartquery)

    #  cartSnippet = cartcursor.fetchone

    for (item, price) in cartcursor:
        carttable += "<tr><td>%s</td>" % item
        carttable += "<td>%s</td>" % price
        carttable += '''<td> <form action="{{ url_for('admin')}}" method="post" autocomplete="off">                   <input type="hidden" name="item_name" value="%s">''' % item
        carttable += '''<input type="number" name="new_price" step="0.01" placeholder="2.99"></td><td><input type="submit" class="btn" value="Change Price" name="Change Price"></td></form></tr>'''

    cartcursor.close()
    carttable += "</table></br>"
    f = open("templates/admin.html", "w")
    f.write(htmlprologue)
    f.write(carttable)
    f.write(htmlepilogue)
    f.close()
if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True)
    app.run()
