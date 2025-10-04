# users_search.py
import aiohttp
import asyncio
import json
import os
import sys
from tqdm.asyncio import tqdm_asyncio

PROFILE_URL = "https://www.jbzd.com.pl/mikroblog/user/profile/"
SEARCH_URL = "https://m.jbzd.com.pl/search/users?page=1&per_page=12&phrase={}"
HEADERS = {
    "accept": "application/json",
    "user-agent": "Mozilla/5.0"
}
MAX_RETRIES = 10
CONCURRENCY = 5


async def fetch_json(session, url, retries=MAX_RETRIES):
    """
    Pobiera dane JSON z ponownymi próbami przy błędach sieciowych.
    - 404: od razu zwraca None (pomijamy użytkownika)
    - inne błędy: ponawia do skutku (do MAX_RETRIES)
    """
    for attempt in range(1, retries + 1):
        try:
            async with session.get(url, headers=HEADERS, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    # użytkownik nie istnieje → pomijamy bez retry
                    return None
                else:
                    print(f"❌ HTTP {resp.status} dla {url} (próba {attempt}/{retries})")
        except Exception as e:
            print(f"⚠️ Błąd przy {url} (próba {attempt}/{retries}): {e}")

        # małe opóźnienie między próbami (rosnące)
        await asyncio.sleep(min(2 * attempt, 10))

    print(f"🚨 Nie udało się pobrać {url} po {retries} próbach")
    return None


async def fetch_user_name(session, user_id):
    """Pobiera nazwę użytkownika po ID."""
    data = await fetch_json(session, f"{PROFILE_URL}{user_id}")
    if data and data.get("status") == "success":
        return data["user"]["name"]
    return None


async def fetch_user_search(session, name):
    """Pobiera dane wyszukiwania po nazwie użytkownika."""
    data = await fetch_json(session, SEARCH_URL.format(name))
    if data and data.get("status") == "success":
        return data["values"]
    return []


async def main(start_id, end_id, output_file):
    timeout = aiohttp.ClientTimeout(total=60)
    connector = aiohttp.TCPConnector(limit_per_host=CONCURRENCY)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        sem = asyncio.Semaphore(CONCURRENCY)
        all_results = []

        async def worker(user_id):
            async with sem:
                name = await fetch_user_name(session, user_id)
                if not name:
                    return None  # brak użytkownika lub 404 → pomijamy
                users_data = await fetch_user_search(session, name)
                if users_data:
                    return {"name": name, "results": users_data}
                return None

        tasks = [worker(uid) for uid in range(start_id, end_id + 1)]

        for result in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc=f"Pobieranie {output_file}"):
            data = await result
            if data:
                all_results.append(data)

    os.makedirs("output", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for item in all_results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Zapisano dane dla {len(all_results)} użytkowników do {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Użycie: python users_search.py <start_id> <end_id> <output_file>")
        sys.exit(1)

    start_id = int(sys.argv[1])
    end_id = int(sys.argv[2])
    output_file = sys.argv[3]

    asyncio.run(main(start_id, end_id, output_file))
