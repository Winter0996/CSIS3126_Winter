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

#  Setup path for 'static/uploads'
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Root Route is the Registratoin page
@app.route('/', methods=['GET', 'POST'])
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
                       (username, email, hashed_password))
        conn.commit()
        cursor.close()

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
        cursor.execute('''SELECT id, password FROM users WHERE username = %s''', (username,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            # Debugging, print the hashed password in the DB
            print(f"Stored hashed password: {user[1]}")

            # Chech if hashed password matches the entered password
            if check_password_hash(user[1], password):
                session['user_id'] = user[0] # store user id in session
                flash('Login successful', 'success')
                return redirect(url_for('home'))
            else:
                #Debugging: incorrect password
                print("Password mismatch")
                flash('invalid credentials, please try again', 'danger')
        else:
            # Debugging: user not founf
            print("User not found")
            flash('invalid credentials, please try again', 'danger')

    return render_template('login.html')

# Home route
@app.route('/home', methods=['GET'])
def home(): 
    if 'user_id' not in session:
        return redirect(url_for('login'))  # redirect to login if user is not logged in 
    
    # fetch all posts along with comments and like counts
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute('''
        SELECT posts.id, posts.content, posts.image_url, posts.created_at, 
               users.username, COUNT(likes.id) AS like_count
        FROM posts
        LEFT JOIN users ON posts.user_id = users.id
        LEFT JOIN likes ON posts.id = likes.post_id
        GROUP BY posts.id
        ORDER BY posts.created_at DESC
    ''')

    posts = cursor.fetchall()
    cursor.close()
    return render_template('home.html', posts=posts)

# Route to create a new post
@app.route('/post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = request.form['content']
    image = request.files.get('image') # Get the uploaded image, if any

    image_url = None
    if image:
        filename = secure_filename(image.filename)
        image_url = os.path.join('static', 'uploads', filename)
        image.save(os.path.join('app', image_url))

        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute('''
               INSERT INTO posts (user_id, content, image_url)
               VALUES (%s, %s, %s)
        ''',    (session['user_id'], content, image_url))
        conn.commit()
        cursor.close()

        flash('Post created successfully!', 'success')
        return redirect(url_for('home'))
    
# Route to leave a comment
@app.route('/comment', methods=['POST'])
def add_comment():
    if 'user_id' not in session:
        flash('You need to log in to comment', 'danger')
        return redirect(url_for('login'))
    
    post_id = request.form['post_id']
    content = request.form['comment_content']

    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(''' 
           INSERT INTO comments (user_id, post_id, content)
           VALUES (%s, %s, %s)
    ''', (session['user_id'], post_id, content))
    conn.commit()
    cursor.close()

    flash('Comment added successfully', 'success')
    return redirect(url_for('home'))

# Route to like a post
@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    if 'user_id' not in session:
        flash('You need to log in to like a post,', 'danger')
        return redirect(url_for('login'))
    
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(''' 
           INSERT IGNORE INTO likes (user_id, post_id)
           VALUES (%s, %s)
    ''', (session['user_id'], post_id))
    conn.commit()
    cursor.close()

    flash('Post liked!', 'success')
    return redirect(url_for('home'))

# Manage Profile route
@app.route('/profile', methods=['GET'])  
def manage_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute(''' SELECT username, bio, avatar_url FROM users WHERE id = %s''', (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()

    return render_template('manage_profile.html', user=user)

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    bio = request.form.get('bio')
    avatar = request.files.get('avatar')
    avatar_url = None

    if avatar:
        filename = secure_filename(avatar.filename)
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        avatar.save(avatar_path)
        avatar_url = f'uploads/{filename}'

        conn = mysql.connection
        cursor = conn.cursor()
        if avatar_url: 
            cursor.execute('''UPDATE users SET bio = %s, avatar_url = %s WHERE id = %s''', (bio, avatar_url, session['user_id']))
        else:
            cursor.execute('''UPDATE users SET bio = %s WHERE id = %s''', (bio, session['user_id']))

        conn.commit()
        cursor.close()

        flash('Profile updated!', 'success')
        return redirect(url_for('manage_profile'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None) # remove user_id from session
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Run the application
if __name__== "__main__":
    app.run(debug=True)