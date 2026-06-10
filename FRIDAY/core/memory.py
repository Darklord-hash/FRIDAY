import sqlite3
import os
from datetime import datetime

# DB sits in friday/ root folder
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'friday_memory.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Conversation history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    # Long-term memory (key-value facts)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("[FRIDAY] Memory DB initialized.")


# ── Short-term Memory (session only) ─────────────────────
short_term = []

def add_to_short_term(role, message):
    short_term.append({
        "role": role,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    # Keep only last 10 exchanges
    if len(short_term) > 10:
        short_term.pop(0)

def get_short_term():
    return short_term

def clear_short_term():
    short_term.clear()
    print("[FRIDAY] Short-term memory cleared.")


# ── Long-term Memory (persistent) ────────────────────────
def save_memory(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO memory (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
    ''', (key, value, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_memory(key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM memory WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None

def get_all_memories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value, updated_at FROM memory')
    rows = cursor.fetchall()
    conn.close()
    return [{"key": r['key'], "value": r['value'], "updated_at": r['updated_at']} for r in rows]

def delete_memory(key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM memory WHERE key = ?', (key,))
    conn.commit()
    conn.close()
    print(f"[FRIDAY] Forgot: {key}")


# ── Conversation History ──────────────────────────────────
def save_conversation(role, message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (role, message, timestamp)
        VALUES (?, ?, ?)
    ''', (role, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_recent_conversations(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, message, timestamp FROM conversations
        ORDER BY id DESC LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r['role'], "message": r['message'], "timestamp": r['timestamp']} for r in reversed(rows)]

def get_conversations_by_date(date_str):
    # date_str format: "2024-01-25"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, message, timestamp FROM conversations
        WHERE timestamp LIKE ?
        ORDER BY id ASC
    ''', (f"{date_str}%",))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r['role'], "message": r['message'], "timestamp": r['timestamp']} for r in rows]

def clear_conversation_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM conversations')
    conn.commit()
    conn.close()
    print("[FRIDAY] Conversation history cleared.")


if __name__ == "__main__":
    init_db()

    # Test conversation history
    save_conversation("user", "What's the time?")
    save_conversation("friday", "It's 5:30 PM Boss.")
    save_conversation("user", "Open YouTube")
    save_conversation("friday", "Opening YouTube for you Boss.")

    print("\n── Recent Conversations ──")
    for entry in get_recent_conversations():
        print(f"[{entry['timestamp']}] {entry['role'].upper()}: {entry['message']}")