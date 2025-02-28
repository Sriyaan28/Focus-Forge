 # Flask backend
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)

# Database file
DATABASE = 'database.db'

# Helper function to get the database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

# Initialize the database (run this once to create tables)
def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (friend_id) REFERENCES users(id)
            )
        ''')
        db.commit()

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Login
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if user and check_password_hash(user['password_hash'], password):
        return jsonify({'success': True, 'message': 'Login successful', 'user_id': user['id']})
    return jsonify({'success': False, 'message': 'Invalid email or password'})

# Signup
@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']
    password_hash = generate_password_hash(password)
    db = get_db()
    try:
        db.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', (email, password_hash))
        db.commit()
        return jsonify({'success': True, 'message': 'Signup successful'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Email already exists'})

# Fetch tasks
@app.route('/tasks', methods=['GET'])
def get_tasks():
    user_id = request.args.get('user_id')
    db = get_db()
    tasks = db.execute('SELECT * FROM tasks WHERE user_id = ?', (user_id,)).fetchall()
    return jsonify([dict(task) for task in tasks])

# Add task
@app.route('/tasks', methods=['POST'])
def add_task():
    user_id = request.form['user_id']
    task = request.form['task']
    db = get_db()
    db.execute('INSERT INTO tasks (user_id, task) VALUES (?, ?)', (user_id, task))
    db.commit()
    return jsonify({'success': True, 'message': 'Task added'})

# Fetch friends
@app.route('/friends', methods=['GET'])
def get_friends():
    user_id = request.args.get('user_id')
    db = get_db()
    friends = db.execute('''
        SELECT users.email FROM friends
        JOIN users ON friends.friend_id = users.id
        WHERE friends.user_id = ?
    ''', (user_id,)).fetchall()
    return jsonify([dict(friend) for friend in friends])

# Run the app
if __name__ == '__main__':
    init_db()  # Initialize the database (run once)
    app.run(debug=True)