"""
view_attendance.py — View and export attendance reports

HOW TO USE:
  python view_attendance.py              → today's attendance
  python view_attendance.py --date 2026-06-07   → specific date
  python view_attendance.py --all        → all records ever
  python view_attendance.py --export     → export to CSV file
  python view_attendance.py --students   → list all registered students
"""

import sqlite3
import csv
import argparse
from datetime import date, datetime
from database import DB_PATH, get_attendance_today, get_attendance_by_date, get_all_students


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_all_records():
    """Return every attendance record from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT name, date, time
        FROM attendance
        ORDER BY date DESC, time ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_summary():
    """Return per-student attendance count."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT name, COUNT(*) as days_present
        FROM attendance
        GROUP BY name
        ORDER BY days_present DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Display functions ─────────────────────────────────────────────────────────

def print_records(records, title="Attendance Report"):
    print()
    print("=" * 52)
    print(f"  {title}")
    print("=" * 52)

    if not records:
        print("  No records found.")
        print("=" * 52)
        return

    print(f"  {'#':<4} {'Name':<20} {'Date':<14} {'Time'}")
    print("-" * 52)
    for i, r in enumerate(records, 1):
        name = r.get("name", "-")
        date_val = r.get("date", "-")
        time_val = r.get("time", "-")
        print(f"  {i:<4} {name:<20} {date_val:<14} {time_val}")

    print("=" * 52)
    print(f"  Total: {len(records)} record(s)")
    print("=" * 52)
    print()


def print_students(students):
    print()
    print("=" * 52)
    print("  Registered Students")
    print("=" * 52)

    if not students:
        print("  No students registered yet.")
        print("  Run register_faces.py to add students.")
        print("=" * 52)
        return

    print(f"  {'#':<4} {'Name':<20} {'Registered On'}")
    print("-" * 52)
    for i, s in enumerate(students, 1):
        reg_date = s["registered"][:10]  # only date part
        print(f"  {i:<4} {s['name']:<20} {reg_date}")

    print("=" * 52)
    print(f"  Total: {len(students)} student(s)")
    print("=" * 52)
    print()


def print_summary():
    summary = get_summary()
    print()
    print("=" * 42)
    print("  Attendance Summary (All Time)")
    print("=" * 42)

    if not summary:
        print("  No attendance records yet.")
        print("=" * 42)
        return

    print(f"  {'Name':<24} {'Days Present'}")
    print("-" * 42)
    for s in summary:
        print(f"  {s['name']:<24} {s['days_present']}")

    print("=" * 42)
    print()


# ── Export ────────────────────────────────────────────────────────────────────

def export_to_csv(records, filename=None):
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"attendance_export_{timestamp}.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "date", "time"])
        writer.writeheader()
        writer.writerows(records)

    print(f"\n  [Export] Saved {len(records)} record(s) to '{filename}'")
    return filename


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Face Attendance System — View & Export Reports"
    )
    parser.add_argument("--date",     type=str,  help="View specific date (YYYY-MM-DD)")
    parser.add_argument("--all",      action="store_true", help="View all records")
    parser.add_argument("--export",   action="store_true", help="Export to CSV")
    parser.add_argument("--students", action="store_true", help="List all students")
    parser.add_argument("--summary",  action="store_true", help="Show attendance summary")
    args = parser.parse_args()

    if args.students:
        print_students(get_all_students())

    elif args.summary:
        print_summary()

    elif args.all:
        records = get_all_records()
        print_records(records, title="All Attendance Records")
        if args.export:
            export_to_csv(records)

    elif args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print("[ERROR] Date format should be YYYY-MM-DD — e.g. 2026-06-07")
            return
        records = get_attendance_by_date(args.date)
        print_records(records, title=f"Attendance on {args.date}")
        if args.export:
            export_to_csv(records)

    else:
        # Default — today
        today   = date.today().isoformat()
        records = get_attendance_today()
        print_records(records, title=f"Today's Attendance — {today}")
        if args.export:
            export_to_csv(records)


if __name__ == "__main__":
    main()