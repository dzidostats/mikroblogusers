import itertools
import json
import requests
import sys
import time
import random

# --- KONFIGURACJA ---
OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "jbzd_users.jsonl"
START_IDX = int(sys.argv[2]) if len(sys.argv) > 2 else 0
END_IDX = int(sys.argv[3]) if len(sys.argv) > 3 else 17576
PER_PAGE = 50
SLEEP_BETWEEN_REQUESTS = 2  # zwiększone opóźnienie
MAX_PAGES_PER_PHRASE = 20
MAX_RETRIES = 5

def fetch_users(phrase, page=1):
    url = "https://m.jbzd.com.pl/search/users"
    params = {"phrase": phrase, "page": page, "per_page": PER_PAGE}

    for attempt in range(1, MAX_RETRIES+1):
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            wait = attempt * 5
            print(f"429 dla frazy {phrase}, strona {page}, retry za {wait}s")
            time.sleep(wait)
        else:
            print(f"Błąd {response.status_code} dla frazy {phrase}, strona {page}")
            break
    return None

def all_combinations(length=3):
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    for combo in itertools.product(chars, repeat=length):
        yield "".join(combo)

# Wybierz zakres dla tego joba
all_combos = list(all_combinations())[START_IDX:END_IDX]

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for phrase in all_combos:
        page = 1
        print(f"Pobieranie frazy: '{phrase}'")

        while page <= MAX_PAGES_PER_PHRASE:
            data = fetch_users(phrase, page)
            if not data or "values" not in data:
                print(f"Brak danych dla frazy '{phrase}' na stronie {page}, przerywam.")
                break

            for user in data["values"]:
                f.write(json.dumps(user, ensure_ascii=False) + "\n")

            meta = data.get("meta", {})
            if not meta.get("has_more_pages", False):
                break

            page += 1
            # sekwencyjne pobieranie ze zmiennym opóźnieniem
            time.sleep(SLEEP_BETWEEN_REQUESTS + random.uniform(0, 1))

print(f"✅ Zakres {START_IDX}-{END_IDX} zakończony.")
