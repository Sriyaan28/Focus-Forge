from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Add a secret key for session management

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
                password_hash TEXT NOT NULL,
                streak INTEGER DEFAULT 0,
                time_spent INTEGER DEFAULT 0,
                energy_level INTEGER DEFAULT 50
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Dashboard page
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template('home.html')

# Login
@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        return jsonify({'success': True, 'message': 'Login successful', 'user_id': user['id']})
    return jsonify({'success': False, 'message': 'Invalid email or password'})

# Signup
@app.route('/signup', methods=['POST'])
def signup():
    email = request.json['email']
    password = request.json['password']
    password_hash = generate_password_hash(password)
    db = get_db()
    try:
        db.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', (email, password_hash))
        db.commit()
        return jsonify({'success': True, 'message': 'Signup successful'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Email already exists'})

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Fetch tasks
@app.route('/tasks', methods=['GET'])
def get_tasks():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    db = get_db()
    tasks = db.execute('SELECT * FROM tasks WHERE user_id = ?', (user_id,)).fetchall()
    return jsonify([dict(task) for task in tasks])

# Add task
@app.route('/tasks', methods=['POST'])
def add_task():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    task = request.json['task']
    db = get_db()
    db.execute('INSERT INTO tasks (user_id, task) VALUES (?, ?)', (user_id, task))
    db.commit()
    return jsonify({'success': True, 'message': 'Task added'})

# Fetch friends leaderboard
@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    db = get_db()
    leaderboard = db.execute('''
        SELECT email, streak, time_spent FROM users
        ORDER BY streak DESC, time_spent DESC
    ''').fetchall()
    return jsonify([dict(user) for user in leaderboard])

# Update user streak and time spent
@app.route('/update-streak', methods=['POST'])
def update_streak():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    time_spent = request.json['time_spent']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        # Check if the user completed at least 3 tasks today
        tasks_today = db.execute('''
            SELECT COUNT(*) as count FROM tasks
            WHERE user_id = ? AND completed = 1 AND DATE(created_at) = DATE('now')
        ''', (user_id,)).fetchone()
        if tasks_today['count'] >= 3:
            db.execute('UPDATE users SET streak = streak + 1 WHERE id = ?', (user_id,))
        db.execute('UPDATE users SET time_spent = time_spent + ? WHERE id = ?', (time_spent, user_id))
        db.commit()
        return jsonify({'success': True, 'message': 'Streak and time spent updated'})
    return jsonify({'success': False, 'message': 'User not found'})

# Update user energy level
@app.route('/update-energy', methods=['POST'])
def update_energy():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    energy_level = request.json['energy']
    db = get_db()
    db.execute('UPDATE users SET energy_level = ? WHERE id = ?', (energy_level, user_id))
    db.commit()
    return jsonify({'success': True, 'message': 'Energy level updated'})

# Fetch upcoming tasks
@app.route('/upcoming-tasks', methods=['GET'])
def get_upcoming_tasks():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    db = get_db()
    tasks = db.execute('''
        SELECT task FROM tasks
        WHERE user_id = ? AND completed = 0 AND DATE(created_at) >= DATE('now')
        ORDER BY created_at
    ''', (user_id,)).fetchall()
    return jsonify([dict(task) for task in tasks])

# Run the app
if __name__ == '__main__':
    init_db()  # Initialize the database (run once)
    app.run(debug=True)