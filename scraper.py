import itertools
import json
import requests
import time

OUTPUT_FILE = "jbzd_users.jsonl"
PER_PAGE = 50
SLEEP_BETWEEN_REQUESTS = 0.5

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

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for phrase in all_combinations():
        page = 1
        print(f"Pobieranie: '{phrase}' (strona {page})")

        while True:
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

print("✅ Zakończono pobieranie wszystkich kombinacji.")
