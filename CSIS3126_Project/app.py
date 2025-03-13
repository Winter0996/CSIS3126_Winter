# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

# Initialize Flask app and MYSQL connection
app = Flask(__name__)
app.config.from_object('config.Config')

mysql = MySQL(app)

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

   # Hash password before saving into database
        hashed_password = generate_password_hash(password)

        # Insert into database
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (username, email, password) VALUES (%s, %s, %s)''',
                       (username, email, password))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration Successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Chech user credentials 
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM users WHERE username = %s''', (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[3], password): # user[3] is the password column
            session['user_id'] = user[0] # store user ID in session
            flash('Login successful', 'success')
            return redirect(url_for('homepage.html'))
    else:
        flash('Invalid credentials, please try again', 'danger')

    return render_template('login.html')

# Home route
@app.route('/')
def home(): 
    if 'user_id' not in session:
        return redirect(url_for('login'))  # redirect to login if user is not logged in 
    return render_template('homepage.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None) # remove user_id from session
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Run the application
if __name__== "__main__":
    app.run(debug=True)