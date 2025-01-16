import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_users_table()
        self.create_data_sets_table()
        self.create_users_data_sets_table()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    """
    table initializations
    """
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
                         
                -- ON DELETE CASCADE, deletes all user_id entries in this table when user_id is removed from users
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """)
            conn.commit()

    def create_users_data_sets_table(self):
        with self.get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users_data_sets (
                saved_data_set_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id,
                data_set BLOB NOT NULL,
                file_name TEXT NOT NULL,
                server_storage_bytes INTEGER NOT NULL,
                user_max_server_storage_bytes INTEGER NOT NULL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- ON DELETE CASCADE, deletes all user_id entries in this table when user_id is removed from users
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
        
    def get_username(self, user_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None

    def user_exists(self, username):
        """
        Args:
        username ->  str: the username to check their existance

        Returns
        returns True if user exists
        returns False if user does not exist
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))
            # Check if a row is fetched
            return cursor.fetchone() is not None 

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
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT file_name, file_type, data_set, file_size_bytes
                    FROM data_sets
                    WHERE data_set_id = ?
                ''', (dataset_id,))
                result = cursor.fetchone()

                if result:
                    return {
                        'file_name': result[0],
                        'file_type': result[1],
                        'data_set': result[2],  # binary data of the dataset file
                        'file_size': result [3]
                    }
                else:
                    return None

        except Exception as e:
            print(f"Error retrieving dataset: {str(e)}")
            return None

    """
    users_data_sets table functions
    """ 
    def save_user_data_set(self, user_id, data_set, file_name, server_storage_bytes, user_max_server_storage_bytes):
        with self.get_connection() as conn:
            try:
                # add new dataset to data_sets table
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users_data_sets (user_id, data_set, file_name, server_storage_bytes, user_max_server_storage_bytes, saved_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, data_set, file_name, server_storage_bytes, user_max_server_storage_bytes))
                conn.commit()

            except sqlite3.IntegrityError:
                # Handle cases where the data might violate constraints (e.g., duplicate user_id or file_name)
                print(f"Error: Failed to save the dataset for user ID {user_id} and file '{file_name}'.")

    """
    generic database helper functions
    """
    def clear_database(self):
        """
        this method is used to clear the db as i develop
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            for table in tables:
                table_name = table[0]

                # skip internal table
                if table_name == 'sqlite_sequence':
                    continue
                
                # delete all rows from each table
                cursor.execute(f"DELETE FROM {table_name}")
                
                # reset incrementer, so ids continue to start from 1
                cursor.execute(f"UPDATE sqlite_sequence SET seq = 0 WHERE name = '{table_name}'")
            
            # commit changes
            conn.commit()
            print("All tables and sequences cleared")

    def clear_data_sets(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # deltes all rows in the data_sets table
            cursor.execute("DELETE FROM data_sets")
            # reset data_set_id sequence
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='data_sets'")
            conn.commit()
            print("data_sets data cleared")


