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

    
        if( it[0] is None ):
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
    username = session['username']

    cursor = cnx.cursor(buffered = True)
    findBudget = "SELECT monthly_budget FROM user WHERE username= %s"
    cursor.execute(findBudget, (username,))
    budget = cursor.fetchone()
    print(budget[0])
    findItemsIds = "SELECT item_id FROM shopping_cart WHERE username= %s"
    itemsIds = cursor.fetchall();
    
    return render_template('shopping_cart.html')
if __name__ == "__main__":
    app.debug = True
    app.run()
