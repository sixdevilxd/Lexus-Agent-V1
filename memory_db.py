"""Memori percakapan persisten berbasis SQLite.
Riwayat chat tetap tersimpan walau bot di-restart / crash."""
import sqlite3
import json

DB_PATH = "lexus_memory.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            chat_id INTEGER PRIMARY KEY,
            history TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def load_history(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT history FROM conversations WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return []
    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return []


def save_history(chat_id, history_list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    data = json.dumps(history_list, ensure_ascii=False)
    cursor.execute(
        "INSERT OR REPLACE INTO conversations (chat_id, history) VALUES (?, ?)",
        (chat_id, data)
    )
    conn.commit()
    conn.close()


def clear_history(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
