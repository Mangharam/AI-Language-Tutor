import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "tutor.db"

conn = sqlite3.connect(db_path)

try:
    for name, sql in conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
    ):
        print(f"\nTABLE: {name}")
        print(sql, "\n")
finally:
    conn.close()