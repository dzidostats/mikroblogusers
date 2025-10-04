import itertools
import json
import requests
import sys
import time

# --- KONFIGURACJA ---
OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "jbzd_users.jsonl"
START_IDX = int(sys.argv[2]) if len(sys.argv) > 2 else 0
END_IDX = int(sys.argv[3]) if len(sys.argv) > 3 else 17576  # 26^3 = 17576
PER_PAGE = 50
SLEEP_BETWEEN_REQUESTS = 2


def fetch_users(phrase, page=1):
    url = "https://m.jbzd.com.pl/search/users"
    params = {"phrase": phrase, "page": page, "per_page": PER_PAGE}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Błąd {response.status_code} dla frazy {phrase}, strona {page}")
        return None


def all_combinations():
    letters = "abcdefghijklmnopqrstuvwxyz"
    for combo in itertools.product(letters, repeat=3):
        yield "".join(combo)


# Wybierz tylko zakres przypisany do tego joba
all_combos = list(all_combinations())[START_IDX:END_IDX]

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for phrase in all_combos:
        page = 1
        print(f"Pobieranie: '{phrase}' (strona {page})")

        max_pages = 20
        page = 1

        while page <= max_pages:
            data = fetch_users(phrase, page)
            if not data or "values" not in data:
                break  # kończy, jeśli brak danych

            for user in data["values"]:
                f.write(json.dumps(user, ensure_ascii=False) + "\n")

            meta = data.get("meta", {})

            page += 1
            time.sleep(SLEEP_BETWEEN_REQUESTS)

print(f"✅ Zakres {START_IDX}-{END_IDX} zakończony.")
