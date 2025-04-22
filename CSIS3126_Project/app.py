# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import MySQLdb.cursors
import uuid
from helpers import allowed_file
import os

# Initialize Flask app and MYSQL connection
app = Flask(__name__)
app.config.from_object('config.Config')

mysql = MySQL(app)

#  Setup path for 'static/uploads'
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Root Route is the Registration page
@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        print(request.form)  # See what keys Flask is receiving


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
            # Debugging: user not found
            print("User not found")
            flash('invalid credentials, please try again', 'danger')

    return render_template('login.html')

# Home route
@app.route('/home', methods=['GET'])
def home(): 
    user_id = session.get("user_id")
    if 'user_id' not in session:
        return redirect(url_for('login'))  # redirect to login if user is not logged in 
    
    cursor = mysql.connection.cursor()
    
    # fetch all posts with user info and likes
    cursor.execute("""
        SELECT posts.id, posts.content, posts.image_url, posts.created_at,
               users.username, posts.likes, users.avatar_url
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
    """)
    posts = cursor.fetchall()

    # Fetch comments for each post
    comments_post = []
    for post in posts:
        post_id = post[0]
        cursor.execute("""
                       SELECT users.avatar_url, users.username, comments.content
                       FROM comments
                       JOIN users ON comments.user_id = users.id
                       WHERE comments.post_id = %s
                       ORDER BY comments.created_at ASC
                       """, (post_id,))
        comment_rows = cursor.fetchall()
        comment_data = '|||'.join(['__SEP__'.join(row) for row in comment_rows])

        # Check if user liked this post
        cursor.execute("""
                       SELECT 1 FROM likes WHERE user_id = %s AND post_id = %s
                       """, (user_id, post_id))
        user_liked = cursor.fetchone() is not None

        comments_post.append(post +(comment_data, user_liked))
    

    cursor.close()
    return render_template('home.html', posts=comments_post)

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
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    cursor = mysql.connection.cursor()

    # Check if user already liked this post 
    cursor.execute("Select 1 FROM likes WHERE user_id = %s AND post_id = %s", (user_id, post_id))
    already_liked = cursor.fetchone()

    if already_liked:
        # Unlike post
        cursor.execute("DELETE FROM likes WHERE user_id = %s AND post_id = %s", (user_id, post_id))
    else:
        # like post
        cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (%s, %s)", (user_id, post_id))

    #Update total like count
    cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = %s", (post_id,))
    like_count = cursor.fetchone()[0]

    # fetch new like count 
    cursor.execute("UPDATE posts SET likes = %s WHERE id = %s", (like_count, post_id))
    mysql.connection.commit()
    cursor.close()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"new_like_count": like_count})
    else:
        return redirect(url_for("home"))

# Route to create a new post
@app.route('/post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = request.form.get('content', '').strip()
    image = request.files.get('image') # Get the uploaded image, if any
    image_url = None

    # Ensure content or image exists 
    if not content and not image:
        flash('Post must contain text or an image.', 'warning')
        return redirect(url_for('home'))

    # Process image
    if image and image.filename != '':
        if allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = os.path.join('uploads', filename).replace("\\", "/")
        else:
            flash('invalid image format.', 'danger')
            return redirect(url_for('home'))

        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (user_id, content, image_url)
            VALUES (%s, %s, %s)
        ''', (session['user_id'], content, image_url))
        conn.commit()  # Ensure this line executes for all posts
        cursor.close()

        flash('Post created successfully!', 'success')
        return redirect(url_for('home'))
  

@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    chat_with = request.args.get('chat_with', type=int)

    conn = mysql.connection
    cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)

    # Get list of all other users for sidebar
    cursor.execute("SELECT id, username, avatar_url FROM users WHERE id != %s", (session['user_id'],))
    chat_users = cursor.fetchall()

    active_chat_user = None
    messages_data = []  # Renamed from messages to avoid confusion with route function name

    if chat_with:
        # Fetch selected user info
        cursor.execute("SELECT id, username, avatar_url FROM users WHERE id = %s", (chat_with,))
        active_chat_user = cursor.fetchone()


        # If  user exists, fetch messages
        if active_chat_user:
            cursor.execute('''
                SELECT m.*, u.username as sender_username, u.avatar_url as sender_avatar
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE (sender_id = %s AND receiver_id = %s)
                   OR (sender_id = %s AND receiver_id = %s)
                ORDER BY timestamp ASC
            ''', (session['user_id'], chat_with, chat_with, session['user_id']))

            messages_data = cursor.fetchall()

    
    cursor.close()
    return render_template(
        'messaging.html',
        user_id=session['user_id'],
        messages=messages_data,
        chat_users=chat_users,
        active_chat_user=active_chat_user,
        active_chat_id=chat_with
    )


# Route to send a new message
@app.route('/send_message/<int:receiver_id>', methods=['POST'])
def send_message(receiver_id):
    if 'user_id' not in session:
        flash('You must be logged in to send a message', 'danger')
        return redirect(url_for('login'))
    
    content = request.form['message']
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute('''
                   INSERT INTO messages (sender_id, receiver_id, content)
                   VALUES (%s, %s, %s)
                ''', (session['user_id'], receiver_id, content))
    conn.commit()
    cursor.close()

    flash('Message Sent!', 'success')
    return redirect(url_for('messages', chat_with=receiver_id))


# Manage Profile route
@app.route('/profile', methods=['GET'])
def manage_profile():
    if 'user_id' not in session:
        flash("You need to log in first.", "danger")
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch user data
    cursor.execute("SELECT username, email, bio, avatar_url FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    # Fetch total post count
    cursor.execute("SELECT COUNT(*) AS post_count FROM posts WHERE user_id = %s", (user_id,))
    post_count = cursor.fetchone()['post_count'] or 0 # if no posts are found, show 0 

    cursor.close()

    return render_template('manage_profile.html', user=user, post_count=post_count)



@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash("You need to log in first.", "danger")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    new_bio = request.form.get('bio')
    new_email = request.form.get('email')

    avatar_file = request.files.get('avatar')
    avatar_url = None

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Checking if user wants to edit profile 
    if avatar_file and allowed_file(avatar_file.filename):
        filename = secure_filename(avatar_file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        avatar_path = os.path.join('static/images', unique_filename)
        avatar_file.save(avatar_path)
        avatar_url = f'images/{unique_filename}'

        # Update avatar
        cursor.execute("""
                       UPDATE users SET bio = %s, email = %s, avatar_url = %s WHERE id = %s
                       """, (new_bio, new_email, avatar_url, user_id))
    else:
            # Only update bio & email
            cursor.execute("""
                           UPDATE users SET bio = %s, email = %s WHERE id = %s
                           """, (new_bio, new_email, user_id))
        
    mysql.connection.commit()
    cursor.close()

    flash("Profile Updated Successfully!", "success")
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