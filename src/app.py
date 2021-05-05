from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import connection_info

app = Flask(__name__)
app.secret_key = 'IUSUCKS'
app.config.update(
    TEMPLATES_AUTO_RELOAD=True
)

cnx = mysql.connector.connect(user=connection_info.MyUser, password=connection_info.MyPassword,
                              host=connection_info.MyHost, database=connection_info.MyDatabase, port='3306')


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'monthlybudget' in request.form:
        username = request.form['username']
        budget = request.form['monthlybudget']

        cursor = cnx.cursor(buffered=True)
        
        # read committed b/c do not want to read data that has not been committed
        # (i.e. if register() has inserted a new user but not yet committed)
        # assuming only one instance per username so no need for repeatable read
        cursor.execute("set session transaction isolation level read committed")
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

    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# deletes a user account and removes data from database
@app.route('/deleteaccount', methods=['GET', 'POST'])
def delete():
    msg = ''
    if 'loggedin' in session:
        if request.method == 'POST' and 'username' in request.form and 'monthlybudget' in request.form:
            username = request.form['username']

            if username != session['username']:
                msg = 'Incorrect username.'
            
            else: 
                budget = request.form['monthlybudget']
                
                cursor = cnx.cursor(buffered = True)
                
                # read committed b/c do not want to read data that has not been committed
                # (i.e. if register() has inserted a new user but not yet committed)
                # assuming only one instance per username so no need for repeatable read
                cursor.execute("set session transaction isolation level read committed")
                query = "SELECT username, monthly_budget FROM user WHERE username = %s"
                cursor.execute(query, (username,))
                account = cursor.fetchone()
                cursor.close()
                if account:
                    # confirm monthly budget
                    if float(budget) == float(account[1]):
                        deletecursor = cnx.cursor(buffered = True)
                        
                        # repeatable read because user could be trying to delete account
                        # as another user is trying to register with same username
                        # only affects one row since username is key so no need for serializable
                        deletecursor.execute("set session transaction isolation level serializable")
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

        return render_template('delete.html', msg=msg)

    else:
        return redirect(url_for('login'))

# a simple page that says hello
@app.route('/index', methods=['GET', 'POST'])
def index():
    msg = ''
    if 'username' in request.form and 'monthlybudget' in request.form:
        username = request.form['username']
        budget = request.form['monthlybudget']
        cursor = cnx.cursor(buffered=True)
        cursor.execute("set session transaction isolation level read committed")
        query = "SELECT * FROM user WHERE username = %s"
        cursor.execute(query, (username,))
        account = cursor.fetchone()
        cursor.close()
        if account:
            msg = 'Log in successful.'
            return render_template('index.html', msg=msg)


@app.route('/paymentmethod', methods=['GET', 'POST'])
def paymentmethod():
    msg = ''
    if 'loggedin' in session:
        username = session['username']
        checkcursor = cnx.cursor(buffered = True)
        
        # read committed b/c do not want to read data that has not been committed
        # (i.e. if register() has inserted a new user but not yet committed)
        # assuming only one instance per username so no need for repeatable read
        checkcursor.execute("set session transaction isolation level read committed")
        checkcursor.callproc('getPaymentFromUsername', [username])
        payment = None
        for result in checkcursor.stored_results():
            payment = result.fetchone()

        checkcursor.close()

        if payment:
            # display existing payment method
            return render_template('disppayment.html', payment = payment)

        elif request.method == 'POST' and 'cardNumber' in request.form and 'cardholderName' in request.form and 'expirationDate' in request.form:
            cardNumber = request.form['cardNumber']
            cardholderName = request.form['cardholderName']
            expirationDate = request.form['expirationDate']

            cursor = cnx.cursor(buffered=True)
            
            # read committed b/c do not want to read data that has not been committed
            # (i.e. if register() has inserted a new user but not yet committed)
            # assuming only one instance per username so no need for repeatable read
            cursor.execute("set session transaction isolation level read committed")
            cursor.callproc('getPaymentFromUsername', [username])
            account = None
            for result in cursor.stored_results():
                account = result.fetchone()

            cursor.close()
            if account:
                # TODO: account can only have one payment method ???
                msg = 'Payment method already exists for this account.'

            else:
                # insert account payment method
                insertcursor = cnx.cursor(buffered=True)
                
                # read committed b/c do not want other transactions to read uncommitted data
                # repeatable read non necessary since only references one row
                insertcursor.execute("set session transaction isolation level read committed")
                query = "INSERT INTO payment VALUES (%s, %s, %s, %s)"
                insertcursor.execute(
                    query, (cardNumber, username, cardholderName, expirationDate,))
                cnx.commit()
                insertcursor.close()
                msg = 'Payment method successfully saved.'

        elif request.method == 'POST':
            msg = 'Please fill in the empty fields.'

        return render_template('payment.html', msg=msg)

    else:
        return redirect(url_for('login'))


@app.route('/purchase', methods=['GET', 'POST'])
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
                <li><a href="{{url_for('budget')}}">Budget</a></li>
                <li class="active"><a href="{{url_for('purchase')}}">Purchase Cart</a></li>
                <li><a href="{{url_for('admin')}}">Admin</a></li>
                <li><a href="{{url_for('transaction_history')}}">Transaction History</a></li>
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
            htmlepilogue = '''
                            </div>
                        </div>
                    </div>
                </body>
            </html>'''

            # create html table for cart info
            
            cartcursor = cnx.cursor(buffered=True)

            # read committed b/c do not want to read data that has not been committed
            # (i.e. if register() has inserted a new user but not yet committed)
            # assuming only one instance per username so no need for repeatable read
            cartcursor.execute("set session transaction isolation level read committed")
            cartcursor.callproc('getCartFromUsername', [session['username']])
            carttable = ""
            count = 0 

            for result in cartcursor.stored_results():
                list = result.fetchall()
            
                for (item, price, quantity) in list:
                    if count == 0:
                        carttable = "<table><tr class='worddark'><td>Item</td><td>Price</td><td>Quantity</td></tr>"
                        count = count + 1

                    carttable += "<tr><td>%s</td>" % item
                    carttable += "<td>%s</td>" % price
                    carttable += "<td>%s</td>" % quantity
                    carttable += '''<td> <form action="{{ url_for('purchase')}}" method="post" autocomplete="off">                   <input type="hidden" name="item_name" value="%s">''' % item

                    carttable += '''<input type="submit" class="btn" value="Remove" name="Remove"><input type="number" name="new_quantity" placeholder="10"><input type="submit" class="btn" value="Change Quantity" name="Change Quantity"></form></td></tr>'''
                
            if count == 0:  # no items in cart
                carttable = '''<p class="worddark">Please add items to the shopping cart before proceeding to checkout.</p></br></br>'''
            else:
                carttable += "</table></br>"
                
            cartcursor.close()
            

            # create html for payment info
            paymentcursor = cnx.cursor(buffered=True)
            
            # read committed b/c do not want to read data that has not been committed
            # (i.e. if register() has inserted a new user but not yet committed)
            # assuming only one instance per username so no need for repeatable read
            paymentcursor.execute("set session transaction isolation level read committed")
            paymentcursor.callproc('getPaymentFromUsername', [session['username']])
            payment = None
            for result in paymentcursor.stored_results():
                payment = result.fetchone()
            paymentcursor.close()

            paymentinfo = ""
            if payment:
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
                htmlepilogue = '''<input type="submit" class="btn" name="purchase" value="Place Order">''' + htmlepilogue
            else:
                htmlepilogue = '''<p class="worddark">Please enter a payment method before proceeding to checkout.</p>''' + htmlepilogue


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
                cursor = cnx.cursor(buffered=True)
                
                # serializable b/c affects multiple rows through multiple queries
                # and do not want other transactions accessing these rows until
                # the delete or update is complete
                cursor.execute("set session transaction isolation level serializable")

                name = request.form['item_name']
                item = cursor.callproc('getItemFromName', [name, 0])
                item_id = item[1]

                deleteItem = 'DELETE FROM shopping_cart WHERE item_id = %s AND username=%s'
                cursor.execute(deleteItem, (item_id, username,))
                cursor.close()
                cnx.commit()
                showCart()

            if 'Change Quantity' in request.form:
                cursor = cnx.cursor(buffered=True)
                
                # serializable b/c affects multiple rows through multiple queries
                # and do not want other transactions accessing these rows until
                # update is complete
                cursor.execute("set session transaction isolation level serializable")
                
                name = request.form['item_name']
                item = cursor.callproc('getItemFromName', [name, 0])
                item_id = item[1]
                
                quantityItem = cursor.callproc('getQuantityFromCart', [session['username'], item_id, 0])
                quantity = quantityItem[1]

                if not request.form['new_quantity'] == '':
                    new_quantity = request.form['new_quantity']
                else:
                    new_quantity = quantity
                updateQuantity = "UPDATE shopping_cart SET quantity=%s WHERE item_id = %s AND username = %s"
                cursor.execute(
                    updateQuantity, (new_quantity, item_id, username, ))
                cursor.close()
                cnx.commit()
                showCart()
        if 'purchase' in request.form:
            print("createNewTransaction")
            transactionID = createNewTransaction()  # create new transaction entry
            # move items in user's cart to transaction-item relation
            transferCart(transactionID)
            # store user's payment info with a purchase
            storePurchase(transactionID)
            clearCart()  # clear user's shopping cart
            showCart()

            msg = 'Order successfully placed!'
        return render_template("purchase.html", msg=msg)

    else:
        return redirect(url_for('login'))


def clearCart():
    cursor = cnx.cursor(buffered=True)
    
    # serializable b/c delete affects multiple rows and do not want to
    # purchase the same cart multiple times accidentally
    cursor.execute("set session transaction isolation level serializable")
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
                <li class="active"><a href="{{url_for('purchase')}}">Purchase Cart</a></li>
                <li><a href="{{url_for('admin')}}">Admin</a></li>
                <li><a href="{{url_for('transaction_history')}}">Transaction History</a></li>
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
    
    # serializable b/c select affects multiple rows and do not want another
    # transaction to insert into shopping cart until this action is done
    cartcursor.execute("set session transaction isolation level serializable")
    cartcursor.callproc('getCartFromUsername', [session['username']])
    count = 0 

    for result in cartcursor.stored_results():
        list = result.fetchall()

        for (item, price, quantity) in list:
            carttable += "<tr><td>%s</td>" % item
            carttable += "<td>%s</td>" % price
            carttable += "<td>%s</td>" % quantity
            carttable += '''<td> <form action="{{ url_for('purchase')}}" method="post" autocomplete="off">                   <input type="hidden" name="item_name" value="%s">''' % item
            carttable += '''<input type="submit" class="btn" value="Remove" name="Remove"><input type="number" name="new_quantity" placeholder="10"><input type="submit" class="btn" value="Change Quantity" name="Change Quantity"></form></td></tr>'''

    cartcursor.close()
    carttable += "</table></br>"
    # create html for payment info
    paymentcursor = cnx.cursor(buffered=True)
    
    # read committed b/c do not want to read data that has not been committed
    # assuming only one instance per username so no need for repeatable read
    paymentcursor.execute("set session transaction isolation level read committed")
    paymentcursor.callproc('getPaymentFromUsername', [session['username']])
    payment = None
    for result in paymentcursor.stored_results():
        payment = result.fetchone()
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
    cursor = cnx.cursor(buffered=True)
    
    # serializable b/c do not want phantom data if another user tries to
    # perform another transaction at the same time
    cursor.execute("set session transaction isolation level serializable")
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
    cursor = cnx.cursor(buffered=True)
    
    # read committed b/c do not want other transactions to read uncommitted data
    # repeatable read non necessary since only references one row
    cursor.execute("set session transaction isolation level repeatable read")

    # get payment info
    paymentquery = "SELECT payment_id FROM payment WHERE username = %s"
    cursor.execute(paymentquery, (session['username'],))
    payment = cursor.fetchone()
    paymentID = payment[0]

    insertquery = "INSERT INTO purchase VALUES(%s, %s, %s, %s)"
    cursor.execute(insertquery, (session['username'], transactionID,
                                 paymentID, datetime.now().strftime("%m/%d/%Y"),))
    cursor.close()


def transferCart(transactionID):
    # get cart items
    cursor = cnx.cursor(buffered=True)
    
    # repeatable read b/c insert affects multiple rows but phantom data is
    # not a concern since each transaction will have a different id number
    cursor.execute("set session transaction isolation level repeatable read")
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

def showShop(isHighToLow, msg):
    print("msg") 
    print(msg)
    cursor = cnx.cursor(buffered=True)
    
    # read committed b/c do not want to read uncommitted data and updates
    # to items will not happen often (only admins can update price)
    cursor.execute("set session transaction isolation level read committed")
    getItems = ""
    if(isHighToLow):
        getItems = "SELECT item_id, name, price FROM item ORDER BY price DESC"
    else:
        getItems = "SELECT item_id, name, price FROM item ORDER BY price ASC"

    htmlprologue = '''<html lang="en">
    <head>
        <title> payment </title>
        <link rel="stylesheet" href="../static/style.css">
    </head>
    <body>
        <div class="one">
            <div class="sidebar">
                <h1>Menu</h1> 
                <ul>
               <li class="active"><a href="{{url_for('shop')}}">Shop</a></li>
                <li><a href="{{url_for('paymentmethod')}}">Payment Method</a></li>
                <li><a href="{{url_for('budget')}}">Budget</a></li>
                <li><a href="{{url_for('purchase')}}">Purchase Cart</a></li>
                <li><a href="{{url_for('admin')}}">Admin</a></li>
                <li><a href="{{url_for('transaction_history')}}">Transaction History</a></li>
                <li><a href="{{url_for('delete')}}">Delete Account</a></li>
                <li><a href="{{url_for('logout')}}">Logout</a></li>
                </ul>
            </div>
            <div class="content" align="center">
            <div class="header">
                    <h1>Shop</h1>
                </div></br></br>
            <h1>{{msg}}</h1>
            <form action="{{ url_for('shop')}}" method="post" autocomplete="off">
            <input type="submit" class "btn" value="Low to High" name="Low to High">
                <input type="submit" class "btn" value="High to Low" name="High to Low">
                </form>
    '''
    cursor.execute(getItems)
    carttable = "<table><tr class='worddark'><td>item</td><td>price</td><td>quantity<td></tr>"
    for (item_id, name, price) in cursor:
        print(item_id)
        print(name)
        print(price)


        carttable += '''<tr> <form action="{{ url_for('shop')}}" method="post" autocomplete="off"><td>%s</td>''' % name
        carttable += "<td>%s</td>" % price
    
        #carttable += '''<td><label for="%s">%s</p> '''
        carttable += '''          <input type="hidden" name="item_name" value="%s"></td>''' % name
        carttable += '''
                    <td>
                        <select name="quantity"> 
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                        <option value="5">5</option>
                        <option value="6">6</option>
                        <option value="7">7</option>
                        <option value="8">8</option>
                        <option value="9">9</option>
                        <option value="10">10</option>
                        </select>
                        
                        <input type="submit" class="btn" value="Add" name="Add">
                        </td></tr></form>
            
                ''' 

    cursor.close()
    carttable += "</table></br>"

    htmlepilogue = '''</div>
        
    </div>
</body>
</html>'''
    f = open("templates/shop.html", "w")
    f.write(htmlprologue)
    f.write(carttable)
    f.write(htmlepilogue)
    f.close()


# registers a new user and inserts data into database
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'monthlybudget' in request.form:
        username = request.form['username']
        budget = request.form['monthlybudget']

        cursor = cnx.cursor(buffered=True)
        
        cursor.execute("set session transaction isolation level read committed")
        query = "SELECT * FROM user WHERE username = %s"
        cursor.execute(query, (username,))
        account = cursor.fetchone()
        cursor.close()
        if account:
            msg = 'Username already exists.'
        else:
            insertcursor = cnx.cursor(buffered=True)
            insertcursor.execute("set session transaction isolation level serializable")
            query = "INSERT INTO user VALUES (%s, %s)"
            insertcursor.execute(query, (username, budget,))
            cnx.commit()
            insertcursor.close()
            msg = 'New account successfully registered.'

    elif request.method == 'POST':
        msg = 'Please fill in the empty fields.'

    return render_template('register.html', msg=msg)


@app.route('/shop', methods=['GET', 'POST'])
def shop():
    msg = ''
    print("in shop")
    if request.method == 'GET':
       showShop(0, msg)
       print(request.form)
    if request.method == 'POST':
        print("POST")
        if "High to Low" in request.form:
            #high to low
            print("HIGH")
            showShop(1, msg)
        if "Low to High" in request.form:
            print("LOW")

            showShop(0, msg)
        if "Add" in request.form:
            print("post:")
            cursor = cnx.cursor(buffered=True)
            cursor.execute("set session transaction isolation level serializable")
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
            msg = 'Added item'
            if(it is None):
                print("item isnt in shopping cart")
                addToShoppingCart = "INSERT INTO shopping_cart VALUES(%s,%s,%s)"
                cursor.execute(addToShoppingCart,
                            (item_id[0], username, quantity,))
                
            else:
                print("item is in shopping cart")

                item = cursor.fetchone()

                quantityItem = cursor.callproc('getQuantityFromCart', [session['username'], item_id, 0])
                quantity = quantityItem[1]
                print(quantity)

                updateQuantity = "UPDATE shopping_cart SET quantity=%s WHERE item_id = %s AND username = %s"
                cursor.execute(
                    updateQuantity, (quantity+1, item_id[0], username, ))
            print("msg")
            
            print(msg)
            cnx.commit()
            cursor.close()
       # addToShoppingCart = "INSERT INTO shopping_cart VALUES(%s,%s,%s)"
        #cursor.execute(addToShoppingCart, (item_id[0], username, quantity,))
        #cursor = cnx.cursor(buffered = True)
    return render_template('shop.html', msg=msg)


def cart_total():
    # find all items
    total = 0
    cursor = cnx.cursor(buffered=True)
    cursor.execute("set session transaction isolation level read committed")
    find_id_and_quantity = "SELECT item_id, quantity FROM shopping_cart WHERE username = %s"
    cursor.execute(find_id_and_quantity, (session['username'],))

    for (item_id, quantity) in cursor:
        # for all items, add price * quantity to total
        find_price = "SELECT price FROM item WHERE item_id = %s"
        cursor.execute(find_price, (item_id,))
        price = cursor.fetchone()[0]
        total += price * quantity
    print(total)
    cursor.close()
    return total


def compute_remaining_budget(cart_total):
    # find budget
    cursor = cnx.cursor(buffered=True)
    cursor.execute("set session transaction isolation level read committed")

    item = cursor.callproc('getBudgetFromUsername', [session['username'], 0])
    budget = item[1]

    remaining_budget = budget - cart_total
    print(remaining_budget)
    cursor.close()
    return remaining_budget


@app.route('/budget', methods=['GET', 'POST'])
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
            cursor = cnx.cursor(buffered=True)
            cursor.execute("set session transaction isolation level serializable")
            changeBudget = "UPDATE user SET monthly_budget = %s WHERE username = %s"
            cursor.execute(changeBudget, (budget, username,))
            cnx.commit()
            cursor.close()
        if 'add_to_budget' in request.form:
            username = session['username']
            print(username)
            # 1. Get budget
            cursor = cnx.cursor(buffered=True)
            cursor.execute("set session transaction isolation level serializable")

            item = cursor.callproc('getBudgetFromUsername', [session['username'], 0])
            budget = item[1]
            add_to_budget = request.form['add_to_budget_i']

            changeBudget = "UPDATE user SET monthly_budget = %s WHERE username = %s"
            newBudget = budget + int(add_to_budget)
            print(newBudget)
            cursor.execute(changeBudget, (newBudget, username,))
    return render_template('budget.html', remaining_budget=remaining_budget)


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
                <li><a href="{{url_for('budget')}}">Budget</a></li>
                <li><a href="{{url_for('purchase')}}">Purchase Cart</a></li>
                <li><a href="{{url_for('admin')}}">Admin</a></li>
                <li class="active"><a href="{{url_for('transaction_history')}}">Transaction History</a></li>
                <li><a href="{{url_for('delete')}}">Delete Account</a></li>
                <li><a href="{{url_for('logout')}}">Logout</a></li>
                                        </ul> 
                                    </div>
                                    <div class="content" align="center">
                                        <div class="header">
                                            <h1>Transaction History</h1>
                                        </div></br></br>
                                       '''
    htmlepilogue = '''
                        </div>
                    </div>
                </body>
            </html>'''

    cartcursor = cnx.cursor(buffered=True)
    cartcursor.execute("set session transaction isolation level read committed")
    cartquery = '''SELECT p.transaction_id, p.date, i.name, it.quantity, t.total
                   FROM purchase p JOIN transaction t on p.transaction_id = t.transaction_id
                                   JOIN item_transaction it on t.transaction_id = it.transaction_id
                                   JOIN item i on it.item_id = i.item_id
                   WHERE username = %s
                   ORDER BY p.transaction_id'''
    cartcursor.execute(cartquery, (session['username'],))

    count = 0;
    prev_transaction_id = -1
    curr_transaction_id = -1
    carttable = ""

    for (transaction_id, date, name, quantity, total) in cartcursor:
        prev_transaction_id = curr_transaction_id
        curr_transaction_id = transaction_id
        if count == 0:
            carttable = '''<table style="width:70%" align:"right"><tr class='worddark'><td>Transaction ID</td><td>Transaction Date</td><td>Item Name</td><td>Item Quantity</td><td>Transaction Total</td></tr>'''
            count = count + 1

        if prev_transaction_id == curr_transaction_id:
            carttable += "<tr><td></td>"
            carttable += "<td></td>"
            carttable += "<td>%s</td>" % name
            carttable += "<td>%s</td>" % quantity
            carttable += "<td>%s</td></tr>" % total
        else: 
            carttable += "<tr><td>%s</td>" % transaction_id
            carttable += "<td>%s</td>" % date
            carttable += "<td>%s</td>" % name
            carttable += "<td>%s</td>" % quantity
            carttable += "<td>%s</td></tr>" % total
    cartcursor.close()

    if count == 0:  # no previous transactions
        carttable = '''<p class="worddark">No previous transactions to display.</p>'''
    else:
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
                <li class="active"><a href="{{url_for('admin')}}">Admin</a></li>
                <li><a href="{{url_for('transaction_history')}}">Transaction History</a></li>
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
        cartcursor.execute("set session transaction isolation level read committed")

        cartcursor.callproc('getItem')
        for result in cartcursor.stored_results():
            list = result.fetchall()

            for (item, price) in list:
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
            cursor.execute("set session transaction isolation level serializable")

            name = request.form['item_name']
            item = cursor.callproc('getItemFromName', [name, 0])
            item_id = item[1]
            new_price = request.form['new_price']

            updatePrice = "UPDATE item SET price=%s WHERE item_id = %s "
            cursor.execute(updatePrice, (new_price, item_id, ))
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
                <li class="active"><a href="{{url_for('admin')}}">Admin</a></li>
                <li><a href="{{url_for('transaction_history')}}">Transaction History</a></li>
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
    cartcursor.execute("set session transaction isolation level read committed")

    cartcursor.callproc('getItem')
    for result in cartcursor.stored_results():
        list = result.fetchall()

        for (item, price) in list:
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
