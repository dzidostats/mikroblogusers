import itertools
import json
import requests
import sys
import time
from math import ceil

# --- KONFIGURACJA ---
OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "jbzd_users.jsonl"
JOB_PART = int(sys.argv[2]) if len(sys.argv) > 2 else 0      # numer joba (opcjonalnie)
TOTAL_JOBS = int(sys.argv[3]) if len(sys.argv) > 3 else 1    # ile jobów w total
PER_PAGE = 50
SLEEP_BETWEEN_REQUESTS = 0.5
MAX_PAGES_PER_PHRASE = 20

# --- FUNKCJE ---
def fetch_users(phrase, page=1):
    url = "https://m.jbzd.com.pl/search/users"
    params = {"phrase": phrase, "page": page, "per_page": PER_PAGE}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Błąd {response.status_code} dla frazy {phrase}, strona {page}")
        return None

def all_combinations(length=3):
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    for combo in itertools.product(chars, repeat=length):
        yield "".join(combo)

def chunkify(lst, n):
    """Podziel listę na n równych części"""
    chunk_size = ceil(len(lst) / n)
    for i in range(n):
        start = i * chunk_size
        end = start + chunk_size
        yield lst[start:end]

# --- GŁÓWNY PROGRAM ---
all_combos = list(all_combinations())
jobs_chunks = list(chunkify(all_combos, TOTAL_JOBS))
my_combos = jobs_chunks[JOB_PART] if JOB_PART < len(jobs_chunks) else []

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for phrase in my_combos:
        page = 1
        print(f"Pobieranie: '{phrase}'")

        while page <= MAX_PAGES_PER_PHRASE:
            data = fetch_users(phrase, page)
            if not data or "values" not in data:
                break

            for user in data["values"]:
                f.write(json.dumps(user, ensure_ascii=False) + "\n")

            meta = data.get("meta", {})
            if not meta.get("has_more_pages", False):
                break

            page += 1
            time.sleep(SLEEP_BETWEEN_REQUESTS)

print(f"✅ Job {JOB_PART} zakończony. Pobrano {len(my_combos)} kombinacji.")
