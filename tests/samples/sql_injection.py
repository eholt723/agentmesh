# Sample: sql_injection.py
# Issues: SQL injection, hardcoded credentials, no password hashing, debug mode in prod

import sqlite3

DB_PATH = "users.db"
ADMIN_PASSWORD = "admin123"  # hardcoded credential

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # SQL injection — user input concatenated directly into query
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()

def login(username, password):
    user = get_user(username)
    if user and user[2] == password:  # plaintext password comparison
        return True
    return False

def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # SQL injection in INSERT
    cursor.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')")
    conn.commit()

def debug_dump():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    print(cursor.fetchall())  # exposes all user data — debug code left in

# Called in production
debug_dump()
