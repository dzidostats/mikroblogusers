import json
import math
import os
import sys
import time
import requests

# --- KONFIGURACJA ---
NUM_JOBS = 20
OUTPUT_DIR = "jobs_output"
URL_USERS = "https://raw.githubusercontent.com/dzidostats/mikroblogusers/refs/heads/main/results/all_names.json"
RETRY_LIMIT = 3
RETRY_DELAY = 2  # sekundy

# --- ODCZYT JOB_INDEX z argumentów workflow ---
if len(sys.argv) < 2:
    print("Usage: python fetch_jbzd_users.py <job_index>")
    sys.exit(1)

job_index = int(sys.argv[1])

# --- POBRANIE LISTY UŻYTKOWNIKÓW ---
response = requests.get(URL_USERS)
usernames = response.json()
print(f"Liczba użytkowników: {len(usernames)}")

# --- PODZIAŁ NA JOBY ---
chunk_size = math.ceil(len(usernames) / NUM_JOBS)
chunks = [usernames[i*chunk_size:(i+1)*chunk_size] for i in range(NUM_JOBS)]
chunk = chunks[job_index]

# --- POBIERANIE DANYCH ---
results = []
for username in chunk:
    for attempt in range(RETRY_LIMIT):
        try:
            url = f"https://jbzd.com.pl/search/users?page=1&per_page=10000&phrase={username}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                results.extend(data.get("values", []))
                break
            else:
                print(f"[Job {job_index+1}] Błąd {r.status_code} dla {username}")
        except Exception as e:
            print(f"[Job {job_index+1}] Błąd przy użytkowniku {username}: {e}")
        time.sleep(RETRY_DELAY)

# --- ZAPIS DO PLIKU JSON ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
filename = os.path.join(OUTPUT_DIR, f"job_{job_index+1}.json")
with open(filename, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"[Job {job_index+1}] Zapisano {len(results)} użytkowników do {filename}")
