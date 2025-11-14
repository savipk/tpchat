import sqlite3
from pathlib import Path

db_path = Path("data/data.db")
conn = sqlite3.connect(db_path)
with open("data/schema.sql", "r", encoding="utf-8") as f:
    conn.executescript(f.read())
conn.commit()
conn.close()
print("Initialized", db_path.resolve())
