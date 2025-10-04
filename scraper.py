import itertools
import json
import requests
import sys
import time

# --- KONFIGURACJA ---
OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "jbzd_users.jsonl"
START_IDX = int(sys.argv[2]) if len(sys.argv) > 2 else 0
END_IDX = int(sys.argv[3]) if len(sys.argv) > 3 else 17576  # liczba kombinacji
PER_PAGE = 50
SLEEP_BETWEEN_REQUESTS = 0.5
MAX_PAGES_PER_PHRASE = 20
MAX_RETRIES_429 = 5
INITIAL_DELAY_429 = 5  # sekundy

def fetch_users(phrase, page=1):
    url = "https://m.jbzd.com.pl/search/users"
    params = {"phrase": phrase, "page": page, "per_page": PER_PAGE}
    delay = INITIAL_DELAY_429

    for attempt in range(MAX_RETRIES_429):
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print(f"❌ 429 dla frazy '{phrase}', strona {page}. Retry w {delay}s...")
            time.sleep(delay)
            delay *= 2  # opcjonalny exponential backoff
        else:
            print(f"❌ Błąd {response.status_code} dla frazy '{phrase}', strona {page}")
            return None

    print(f"❌ Brak odpowiedzi po {MAX_RETRIES_429} próbach dla frazy '{phrase}', strona {page}")
    return None

def all_combinations(length=3):
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    for combo in itertools.product(chars, repeat=length):
        yield "".join(combo)

# Wybieramy zakres dla tego joba
all_combos = list(all_combinations())[START_IDX:END_IDX]

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for phrase in all_combos:
        page = 1
        print(f"Pobieranie frazy: '{phrase}'")

        while page <= MAX_PAGES_PER_PHRASE:
            data = fetch_users(phrase, page)
            if not data or "values" not in data or not data["values"]:
                print(f"Brak danych dla frazy '{phrase}' na stronie {page}, przerywam.")
                break

            for user in data["values"]:
                f.write(json.dumps(user, ensure_ascii=False) + "\n")

            meta = data.get("meta", {})
            if not meta.get("has_more_pages", False):
                break  # koniec stron dla tej frazy

            page += 1
            time.sleep(SLEEP_BETWEEN_REQUESTS)

print(f"✅ Zakres {START_IDX}-{END_IDX} zakończony.")
