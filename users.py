# users.py
import aiohttp
import asyncio
import json
import os
import sys
from tqdm.asyncio import tqdm_asyncio

BASE_URL = "https://www.jbzd.com.pl/mikroblog/user/profile/"
HEADERS = {
    "accept": "application/json",
    "user-agent": "Mozilla/5.0"
}
MAX_RETRIES = 10
CONCURRENCY = 5  # ile równoległych zapytań na hosta

async def fetch_user(session, user_id):
    url = f"{BASE_URL}{user_id}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, headers=HEADERS, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    return None  # użytkownik nie istnieje
                else:
                    print(f"❌ HTTP {resp.status} dla user {user_id}, próba {attempt}")
        except Exception as e:
            print(f"⚠️ Błąd przy user {user_id}, próba {attempt}: {e}")
        await asyncio.sleep(1 * attempt)
    print(f"🚨 Nie udało się pobrać user {user_id} po {MAX_RETRIES} próbach")
    return None

async def main(start_id, end_id, output_file):
    timeout = aiohttp.ClientTimeout(total=60)
    connector = aiohttp.TCPConnector(limit_per_host=CONCURRENCY)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        all_users = []

        sem = asyncio.Semaphore(CONCURRENCY)

        async def worker(user_id):
            async with sem:
                data = await fetch_user(session, user_id)
                if data and data.get("status") == "success":
                    return data["user"]
                return None

        tasks = [worker(uid) for uid in range(start_id, end_id + 1)]

        for result in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc=f"Pobieranie {output_file}"):
            user = await result
            if user:
                all_users.append(user)

    os.makedirs("output", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for user in all_users:
            f.write(json.dumps(user, ensure_ascii=False) + "\n")
    print(f"✅ Zapisano {len(all_users)} użytkowników do {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Użycie: python users.py <start_id> <end_id> <output_file>")
        sys.exit(1)
    start_id = int(sys.argv[1])
    end_id = int(sys.argv[2])
    output_file = sys.argv[3]
    asyncio.run(main(start_id, end_id, output_file))
