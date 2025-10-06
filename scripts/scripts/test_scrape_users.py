#!/usr/bin/env python3
"""
Asynchroniczny testowy scraper użytkowników JBZD
Autor: ChatGPT (GPT-5)
Opis:
 - Pobiera listę nazw z results/all_names.json
 - Dzieli je między joby (parametry --total-jobs i --job-index)
 - Wysyła zapytania do https://jbzd.com.pl/search/users?page=1&per_page=10000&phrase=<nazwa>
 - Równoległość w ramach joba kontroluje --concurrency (domyślnie 5)
 - Zapisuje wyniki do results/users_test/test_part_<n>.json
"""

import asyncio
import aiohttp
import json
import os
import math
from pathlib import Path
from aiohttp import ClientError

# -------------------------------
# USTAWIENIA ZMIENNE I ŚRODOWISKOWE
# -------------------------------
JOB_INDEX = int(os.getenv("JOB_INDEX", "0"))
TOTAL_JOBS = int(os.getenv("TOTAL_JOBS", "20"))
TEST_COUNT = int(os.getenv("TEST_COUNT", "20000"))  # liczba nazw do testu (łącznie, zostanie podzielona)
CONCURRENCY = int(os.getenv("CONCURRENCY", "5"))
MAX_RETRIES = 2
TIMEOUT = 10.0

# -------------------------------
# WCZYTANIE LISTY UŻYTKOWNIKÓW
# -------------------------------
all_names_path = Path("results/all_names.json")
if not all_names_path.exists():
    raise FileNotFoundError("Nie znaleziono pliku results/all_names.json — wgraj go z nazwami użytkowników.")

with open(all_names_path, encoding="utf-8") as f:
    all_names = json.load(f)

# ogranicz listę do TEST_COUNT użytkowników
names = all_names[:TEST_COUNT]

# Podział na joby (równy chunk)
chunk_size = math.ceil(len(names) / TOTAL_JOBS)
start = JOB_INDEX * chunk_size
end = min(start + chunk_size, len(names))
chunk = names[start:end]

print(f"🔹 JOB {JOB_INDEX+1}/{TOTAL_JOBS} → {len(chunk)} użytkowników ({start}–{end-1})")

# -------------------------------
# PRZYGOTOWANIE WYJŚCIA
# -------------------------------
output_dir = Path("results/users_test")
output_dir.mkdir(parents=True, exist_ok=True)
outfile = output_dir / f"test_part_{JOB_INDEX+1}.json"

# -------------------------------
# FUNKCJA ASYNCHRONICZNA
# -------------------------------
SEM = asyncio.Semaphore(CONCURRENCY)
BASE_URL = "https://jbzd.com.pl/search/users?page=1&per_page=10000&phrase={}"

async def fetch_user(session: aiohttp.ClientSession, name: str):
    """Pobierz dane o użytkowniku z jbzd.com.pl"""
    url = BASE_URL.format(name)
    for attempt in range(1, MAX_RETRIES + 2):  # próba + retry
        try:
            async with SEM:
                async with session.get(url, timeout=TIMEOUT) as resp:
                    data = await resp.json(content_type=None)
                    return {"name": name, "status": resp.status, "response": data}
        except (asyncio.TimeoutError, ClientError) as e:
            if attempt <= MAX_RETRIES:
                delay = 0.5 * attempt
                print(f"⚠️ Retry {attempt}/{MAX_RETRIES} for {name} after {delay:.1f}s ({e})")
                await asyncio.sleep(delay)
                continue
            return {"name": name, "error": str(e)}
        except Exception as e:
            return {"name": name, "error": str(e)}

async def run_all():
    connector = aiohttp.TCPConnector(limit_per_host=CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_user(session, n) for n in chunk]
        results = []
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            res = await coro
            results.append(res)
            if i % 50 == 0 or i == len(chunk):
                print(f"Progress: {i}/{len(chunk)}")
        return results

# -------------------------------
# URUCHOMIENIE
# -------------------------------
async def main():
    print(f"🚀 Start JOB {JOB_INDEX+1} (concurrency={CONCURRENCY})")
    results = await run_all()
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ Zapisano {len(results)} rekordów do {outfile}")

if __name__ == "__main__":
    asyncio.run(main())
