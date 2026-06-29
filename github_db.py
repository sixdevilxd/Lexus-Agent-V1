"""Penyimpanan token GitHub pengguna dengan enkripsi (Fernet).
Token dienkripsi sebelum disimpan ke SQLite. Kunci enkripsi otomatis
dibuat di `secret.key` (wajib masuk .gitignore, jangan pernah di-commit)."""
import os
import sqlite3
import logging
from cryptography.fernet import Fernet, InvalidToken

DB_PATH = "github_tokens.db"
KEY_PATH = "secret.key"

_cipher = None


def _get_cipher():
    """Muat kunci enkripsi dari secret.key, atau buat otomatis bila belum ada."""
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, "rb") as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_PATH, "wb") as f:
            f.write(key)
        try:
            os.chmod(KEY_PATH, 0o600)  # hanya pemilik yang bisa baca
        except Exception:
            pass
        logging.info("secret.key baru dibuat untuk enkripsi token GitHub.")
    return Fernet(key)


def cipher():
    global _cipher
    if _cipher is None:
        _cipher = _get_cipher()
    return _cipher


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
    """Enkripsi token lalu simpan."""
    encrypted = cipher().encrypt(token.encode("utf-8")).decode("utf-8")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_tokens (chat_id, access_token) VALUES (?, ?)",
        (chat_id, encrypted)
    )
    conn.commit()
    conn.close()


def get_token(chat_id):
    """Ambil & dekripsi token. Return None bila tidak ada / gagal dekripsi."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT access_token FROM user_tokens WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    try:
        return cipher().decrypt(row[0].encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        # Token lama (plaintext) atau kunci berubah -> paksa login ulang
        logging.warning(f"Gagal dekripsi token chat_id={chat_id}. Perlu login ulang.")
        return None


def delete_token(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_tokens WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
