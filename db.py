import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("logs.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        style TEXT,
        action TEXT,
        decision_time REAL,
        timestamp TEXT
    )""")
    conn.commit()
    conn.close()

def log_action(student_id, style, action, decision_time):
    conn = sqlite3.connect("logs.db")
    conn.execute("INSERT INTO logs (student_id, style, action, decision_time, timestamp) VALUES (?, ?, ?, ?, ?)",
                 (student_id, style, action, decision_time, str(datetime.now())))
    conn.commit()
    conn.close()

def get_student_history(student_id, limit=5):
    conn = sqlite3.connect("logs.db")
    rows = conn.execute("SELECT action FROM logs WHERE student_id=? ORDER BY id DESC LIMIT ?",
                         (student_id, limit)).fetchall()
    conn.close()
    return [r[0] for r in rows]