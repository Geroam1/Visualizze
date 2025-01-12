import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_users_table()
        self.create_data_sets_table()

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

    def create_data_sets_table(self):
         with self.get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS data_sets (
                data_set_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_set BLOB NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """)
            conn.commit()

    """
    user table functions
    """
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

    """
    data_sets table functions
    """ 
    def add_data_set(self, user_id, file_name, file_type, file_size, data_set):
        with self.get_connection() as conn:
            try:
                # add new dataset to data_sets table
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO data_sets (user_id, file_name, file_type, file_size_bytes, uploaded_at, data_set)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (user_id, file_name, file_type, file_size, data_set))

                dataset_id = cursor.lastrowid
                conn.commit()
                return dataset_id
            except sqlite3.IntegrityError:
                # Handle cases where the data might violate constraints (e.g., duplicate user_id or file_name)
                print(f"Error: Failed to add the dataset for user ID {user_id} and file '{file_name}'.")
    
    
    def get_data_set_by_id(self, dataset_id):
        try:
            # query to get data set of user_id
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT file_name, file_type, data_set
                FROM data_sets
                WHERE data_set_id = ?
            ''', (dataset_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                # return data as dictionary
                return {
                    'file_name': result[0],
                    'file_type': result[1],
                    'data_set': result[2]  # binary data of the dataset file
                }
            else:
                # add error message here later
                return None

        except Exception as e:
            # Handle any potential errors (e.g., database connection issues)
            print(f"Error retrieving dataset: {str(e)}")
            return None

    """
    generic database helper functions
    """
    def clear_database(self):
        with self.get_connection() as conn:
            # deletes all rows in the users table
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users")
            # resets user ids
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")

            # deltes all rows in the data_sets table
            cursor.execute("DELETE FROM data_sets")
            # reset data_set_id sequence
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='data_sets'")
            conn.commit()

    def clear_data_sets(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # deltes all rows in the data_sets table
            cursor.execute("DELETE FROM data_sets")
            # reset data_set_id sequence
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='data_sets'")
            conn.commit()
            print("data_sets data cleared")


