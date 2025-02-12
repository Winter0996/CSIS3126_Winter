# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysql import MYSQL
from werkzeug.utils import secure_filename
import os

# Initialize Flask app and MYSQL connection
app = Flask(__name__)
app.config.from_object('config.Config')

mysql = MYSQL(app)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Insert into the database
        conn = mysql.connect()
        cursor = conn.cursor() 
        cursor.execute('''INSERT INTO users (username,email, password) VALUES   (%s, %s, %s)''',
                                (username, email, password))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration Successful!, please login in.' 'success')
        return redirect(url_for('login'))
    
    return render_template('registration.html')

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check user credentials
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(''' SELECT * FROM users WHERE username = %s AND password = %s''', (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]    # Store user ID in the session
            flash('Login successful', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials, please try again', 'danger')

        return render_template('login.html')

        # Home Route (index.html)
        @app.route('/')
        def index():
            if 'user_id' not in session: 
                return redirect(url_for('login'))
            
            return render_template('index.html')
        
        # Run the application
        if __name__ == "__main__":
            app.run(debug=True)

