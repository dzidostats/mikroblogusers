import sqlite3
from pathlib import Path
import glob

DB_DIR = Path(".")
OUTPUT_DB = DB_DIR / "profiles_full.db"

db_files = sorted(glob.glob(str(DB_DIR / "profiles_*.db")))
print(f"Znaleziono {len(db_files)} plików do scalenia.")

conn_out = sqlite3.connect(OUTPUT_DB)
cur_out = conn_out.cursor()

cur_out.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY,
        name TEXT,
        slug TEXT,
        rank INTEGER,
        active BOOLEAN,
        banned BOOLEAN,
        is_admin BOOLEAN,
        is_moderator BOOLEAN,
        avatar_url TEXT,
        profile_url TEXT
    )
""")
conn_out.commit()

for db_file in db_files:
    print(f"Scalam bazę: {db_file}")
    conn_in = sqlite3.connect(db_file)
    cur_in = conn_in.cursor()
    cur_in.execute("SELECT * FROM profiles")
    rows = cur_in.fetchall()
    cur_out.executemany("""
        INSERT OR IGNORE INTO profiles (
            id, name, slug, rank, active, banned, is_admin, is_moderator, avatar_url, profile_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn_out.commit()
    conn_in.close()

conn_out.close()
print(f"\n✅ Scalenie zakończone! Wynikowa baza: {OUTPUT_DB}")
