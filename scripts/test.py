import json
import math
import os
import requests
from concurrent.futures import ThreadPoolExecutor

# 1. Pobranie listy użytkowników z pliku online
url_users = "https://raw.githubusercontent.com/dzidostats/mikroblogusers/refs/heads/main/results/all_names.json"
response = requests.get(url_users)
usernames = response.json()
print(f"Liczba użytkowników: {len(usernames)}")

# 2. Ustalenie liczby jobów i podział listy
num_jobs = 20
chunk_size = math.ceil(len(usernames) / num_jobs)
chunks = [usernames[i*chunk_size:(i+1)*chunk_size] for i in range(num_jobs)]

# 3. Funkcja pobierająca dane użytkowników z JBZD
def fetch_users(job_index, usernames_chunk):
    results = []
    for username in usernames_chunk:
        try:
            url = f"https://jbzd.com.pl/search/users?page=1&per_page=10000&phrase={username}"
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                results.extend(data.get("values", []))
        except Exception as e:
            print(f"Błąd przy użytkowniku {username}: {e}")
    # Zapis do pliku JSON dla joba
    os.makedirs("jobs_output", exist_ok=True)
    filename = f"jobs_output/job_{job_index+1}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Job {job_index+1} zakończony, zapisano {len(results)} użytkowników")

# 4. Uruchomienie pobierania równolegle w 20 jobach
with ThreadPoolExecutor(max_workers=num_jobs) as executor:
    for i, chunk in enumerate(chunks):
        executor.submit(fetch_users, i, chunk)

print("Wszystkie joby zakończone, pliki zapisane w folderze 'jobs_output'.")
