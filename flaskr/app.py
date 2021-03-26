import os

from flask import Flask
from flask import render_template,redirect, url_for,request
from flask import make_response

import mysql.connector
from mysql.connector import Error
from addUser import addUser 


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/index.html', methods=['GET','POST'])
    def index():
        name = request.form.get('name') 
        user_id = request.form.get('id')    # access the data inside 
        monthlybudget= request.form.get('monthly_budget')
        message="User added to the database"
        print( name)
        print(user_id)
        print(monthlybudget)
        addUser(user_id, name, monthlybudget)
        return render_template('index.html', message=message)
    @app.route('/results.html')
    def results():
       return render_template('results.html')
    return app
app = create_app()