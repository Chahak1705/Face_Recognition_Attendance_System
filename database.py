"""
database.py — SQLite setup and helper functions
Face Attendance System
"""

import sqlite3
from datetime import date, datetime

DB_PATH = "attendance.db"


def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets us access columns by name
    return conn


def init_db():
    """Create tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Students table — stores name + when they were registered
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL UNIQUE,
            registered TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Attendance table — one row per student per day
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            name       TEXT    NOT NULL,
            date       TEXT    NOT NULL,
            time       TEXT    NOT NULL,
            UNIQUE(student_id, date),            -- prevent duplicate entries
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialised successfully.")


def add_student(name: str):
    """Register a new student. Ignores if already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO students (name) VALUES (?)", (name,)
        )
        conn.commit()
        if cursor.rowcount:
            print(f"[DB] Student '{name}' registered.")
        else:
            print(f"[DB] Student '{name}' already exists — skipped.")
    finally:
        conn.close()


def get_student_id(name: str) -> int | None:
    """Return the student id for the given name, or None if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT id FROM students WHERE name = ?", (name,)
    ).fetchone()
    conn.close()
    return row["id"] if row else None


def mark_attendance(name: str):
    """
    Mark a student present for today.
    Safe to call multiple times — duplicate entries are ignored.
    Returns True if a new record was inserted, False if already marked.
    """
    student_id = get_student_id(name)
    if student_id is None:
        print(f"[DB] Warning: '{name}' not found in students table. Register them first.")
        return False

    today = date.today().isoformat()          # e.g. 2024-06-07
    now   = datetime.now().strftime("%H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO attendance (student_id, name, date, time)
            VALUES (?, ?, ?, ?)
        """, (student_id, name, today, now))
        conn.commit()
        inserted = cursor.rowcount == 1
        return inserted
    finally:
        conn.close()


def get_attendance_today():
    """Return all attendance records for today as a list of dicts."""
    today = date.today().isoformat()
    conn  = get_connection()
    rows  = conn.execute("""
        SELECT name, time FROM attendance
        WHERE date = ?
        ORDER BY time ASC
    """, (today,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_attendance_by_date(query_date: str):
    """Return attendance records for a specific date (format: YYYY-MM-DD)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT name, time FROM attendance
        WHERE date = ?
        ORDER BY time ASC
    """, (query_date,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_students():
    """Return all registered students."""
    conn  = get_connection()
    rows  = conn.execute("SELECT id, name, registered FROM students ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()

    # Register a couple of test students
    add_student("Alice")
    add_student("Bob")
    add_student("Alice")   # should be ignored

    # Mark attendance
    mark_attendance("Alice")
    mark_attendance("Alice")  # duplicate — should be ignored
    mark_attendance("Bob")

    # View today
    print("\n--- Today's Attendance ---")
    for record in get_attendance_today():
        print(f"  {record['name']:20s}  {record['time']}")

    print("\n--- All Students ---")
    for s in get_all_students():
        print(f"  [{s['id']}] {s['name']:20s}  registered: {s['registered']}")