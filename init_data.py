import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'database.db'

def init_data():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Insert initial users
        users = [
            ('user1@example.com', generate_password_hash('password1')),
            ('user2@example.com', generate_password_hash('password2')),
            ('user3@example.com', generate_password_hash('password3'))
        ]
        cursor.executemany('INSERT INTO users (email, password_hash) VALUES (?, ?)', users)

        # Insert initial tasks for user 1
        tasks = [
            (1, 'Task 1 for user 1', 0),
            (1, 'Task 2 for user 1', 0),
            (1, 'Task 3 for user 1', 0)
        ]
        cursor.executemany('INSERT INTO tasks (user_id, task, completed) VALUES (?, ?, ?)', tasks)

        # Insert initial friends for user 1
        friends = [
            (1, 2),
            (1, 3)
        ]
        cursor.executemany('INSERT INTO friends (user_id, friend_id) VALUES (?, ?)', friends)

        conn.commit()
        print("Initial data inserted successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    init_data()
