import sqlite3
import sys
import os

db_path = 'db.sqlite3'

print("--- Running Python DB Check ---")
print(f"Working directory: {os.getcwd()}")
print(f"Checking for database file at: {db_path}")

if not os.path.exists(db_path):
    print(f"ERROR: Database file not found at {db_path}", file=sys.stderr)
    sys.exit(1)

try:
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("Executing query for 'authtoken_token'...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='authtoken_token'")
    result = cursor.fetchone()
    if result:
        print("SUCCESS: Table 'authtoken_token' found.")
    else:
        print("FAILURE: Table 'authtoken_token' NOT FOUND.")
    conn.close()
    print("--- DB Check Finished ---")
except Exception as e:
    print(f"ERROR: An exception occurred: {e}", file=sys.stderr)
    sys.exit(1) 