import itertools
import json
import requests
import sys
import time

# --- KONFIGURACJA ---
OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "jbzd_users.jsonl"
START_IDX = int(sys.argv[2]) if len(sys.argv) > 2 else 0
END_IDX = int(sys.argv[3]) if len(sys.argv) > 3 else None  # None = wszystkie kombinacje
PER_PAGE = 50
SLEEP_BETWEEN_REQUESTS = 2
MAX_PAGES_PER_PHRASE = 20  # pobierz 20 stron dla każdej kombinacji

# Funkcja pobierająca użytkowników dla danej frazy i strony
def fetch_users(phrase, page=1):
    url = "https://m.jbzd.com.pl/search/users"
    params = {"phrase": phrase, "page": page, "per_page": PER_PAGE}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Błąd {response.status_code} dla frazy {phrase}, strona {page}")
        return None

# Generator wszystkich kombinacji liter i cyfr (domyślnie 3-znakowe)
def all_combinations(length=3):
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    for combo in itertools.product(chars, repeat=length):
        yield "".join(combo)

# Wybór zakresu dla tego joba
all_combos = list(all_combinations())
if END_IDX is None:
    END_IDX = len(all_combos)

selected_combos = all_combos[START_IDX:END_IDX]

print(f"✅ Wybrano {len(selected_combos)} kombinacji: indeksy {START_IDX}-{END_IDX-1}")

# Pobieranie danych
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for phrase in selected_combos:
        print(f"Pobieranie frazy: '{phrase}'")
        for page in range(1, MAX_PAGES_PER_PHRASE + 1):
            data = fetch_users(phrase, page)
            if not data or "values" not in data or len(data["values"]) == 0:
                print(f"Brak danych dla frazy '{phrase}' na stronie {page}, przerywam.")
                break

            for user in data["values"]:
                f.write(json.dumps(user, ensure_ascii=False) + "\n")

            time.sleep(SLEEP_BETWEEN_REQUESTS)

print(f"✅ Zakres {START_IDX}-{END_IDX-1} zakończony.")
