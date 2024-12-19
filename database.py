import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_users_table()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_users_table(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_user(self, username, password_hash, email=None):
        with self.get_connection() as conn:
            try:
                # add new user to users table
                conn.execute("""
                    INSERT INTO users (username, password_hash, email)
                    VALUES (?, ?, ?)
                """, (username, password_hash, email))
                conn.commit()
            except sqlite3.IntegrityError:
                # if user already exists
                print(f"User '{username}' already exists!")

    def get_user(self, username):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            # returns user data if exists
            return cursor.fetchone() 

    def authenticate_user(self, username, password):
        user = self.get_user(username)
        if user:
            if check_password_hash(user['password_hash'], password):
                # return user data
                return user
        return None 

    def clear_database(self):
        with self.get_connection() as conn:
            # deletes all rows in the users table
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users")
            # resets user ids
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
            conn.commit()
