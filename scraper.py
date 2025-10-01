import asyncio
import httpx
import random
import aiosqlite
from pathlib import Path
from tqdm import tqdm
import argparse

# --- ARGUMENTY ---
parser = argparse.ArgumentParser()
parser.add_argument("--start_id", type=int, required=True)
parser.add_argument("--end_id", type=int, required=True)
args = parser.parse_args()

START_ID = args.start_id
END_ID = args.end_id

# --- KONFIGURACJA ---
INITIAL_CONCURRENT = 10
MAX_CONCURRENT = 20      # ograniczamy równoległość dla bezpieczeństwa
BATCH_SIZE = 1000
DB_FILE = Path(f"profiles_{START_ID}_{END_ID}.db")
CHECKPOINT_FILE = Path(f"checkpoint_{START_ID}_{END_ID}.txt")
URL_TEMPLATE = "https://m.jbzd.com.pl/mikroblog/user/profile/{id}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://jbzd.com.pl/",
}

stats = {"success": 0, "errors": 0}


# --- INICJALIZACJA BAZY ---
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
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
        await db.commit()


# --- POBIERANIE PROFILU ---
async def fetch(client, user_id, sem, adjust_concurrent):
    url = URL_TEMPLATE.format(id=user_id)
    async with sem:
        for attempt in range(5):
            try:
                resp = await client.get(url, timeout=10)

                if resp.status_code == 404:
                    stats["errors"] += 1
                    return None

                resp.raise_for_status()

                if "application/json" in resp.headers.get("content-type", ""):
                    stats["success"] += 1
                    adjust_concurrent(success=True)
                    # losowe opóźnienie między 0.5 a 1.5s
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    return resp.json()["user"]
                else:
                    stats["errors"] += 1
                    return None

            except Exception:
                stats["errors"] += 1
                adjust_concurrent(success=False)
                wait_time = 2 ** attempt + random.random()
                await asyncio.sleep(wait_time)
        return None


# --- ZAPIS BATCH DO SQLITE ---
async def save_batch(db, batch):
    records = [
        (
            d["id"],
            d["name"],
            d["slug"],
            d["rank"],
            int(d["active"]),
            int(d["banned"]),
            int(d["is_admin"]),
            int(d["is_moderator"]),
            d["avatar_url"],
            d["profile_url"],
        )
        for d in batch
    ]
    await db.executemany("""
        INSERT OR IGNORE INTO profiles (
            id, name, slug, rank, active, banned, is_admin, is_moderator, avatar_url, profile_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    await db.commit()


# --- FUNKCJA GŁÓWNA ---
async def main():
    await init_db()
    current_concurrent = INITIAL_CONCURRENT
    sem = asyncio.Semaphore(current_concurrent)

    def adjust_concurrent(success: bool):
        nonlocal current_concurrent
        if success:
            if current_concurrent < MAX_CONCURRENT:
                current_concurrent += 1
        else:
            current_concurrent = max(1, current_concurrent - 1)
        sem._value = current_concurrent

    # checkpoint
    if CHECKPOINT_FILE.exists():
        last_id = int(CHECKPOINT_FILE.read_text().strip())
        start = last_id + 1
        print(f"🔄 Wznawiam pobieranie od ID {start}")
    else:
        start = START_ID
        print(f"🚀 Rozpoczynam pobieranie od ID {start}")

    batch = []

    async with aiosqlite.connect(DB_FILE) as db:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
            for user_id in tqdm(range(start, END_ID + 1), desc=f"Pobieranie {START_ID}-{END_ID}"):
                data = await fetch(client, user_id, sem, adjust_concurrent)
                if data:
                    batch.append(data)

                if len(batch) >= BATCH_SIZE:
                    await save_batch(db, batch)
                    batch.clear()
                    CHECKPOINT_FILE.write_text(str(user_id))

                tqdm.write(
                    f"✅ Pobrano: {stats['success']} | ❌ Błędy: {stats['errors']} | 🔄 MAX_CONCURRENT: {current_concurrent}"
                )

            if batch:
                await save_batch(db, batch)
                CHECKPOINT_FILE.write_text(str(END_ID))

    print(f"\n✅ Gotowe! Dane zapisane w {DB_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
