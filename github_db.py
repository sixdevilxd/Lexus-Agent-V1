import sqlite3

DB_PATH = "github_tokens.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            chat_id INTEGER PRIMARY KEY,
            access_token TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_token(chat_id, token):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_tokens (chat_id, access_token) VALUES (?, ?)", 
        (chat_id, token)
    )
    conn.commit()
    conn.close()

def get_token(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT access_token FROM user_tokens WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def delete_token(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_tokens WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
