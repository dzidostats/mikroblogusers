import requests
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Pobieranie argumentów z CLI
worker_id = int(sys.argv[1])
workers_total = int(sys.argv[2])
start_id = int(sys.argv[3])
end_id = int(sys.argv[4])
threads = 5  # liczba równoległych wątków
delay_between_requests = 0.3

# Wyznaczenie zakresu ID dla tego workera
total_ids = end_id - start_id + 1
chunk_size = total_ids // workers_total
chunk_start = start_id + (worker_id - 1) * chunk_size
chunk_end = start_id + worker_id * chunk_size - 1 if worker_id < workers_total else end_id

filename = f"404_ids_worker_{worker_id}.txt"
print(f"Worker {worker_id} sprawdza zakres {chunk_start}-{chunk_end} przy {threads} wątkach")

def check_id(user_id):
    url = f"https://m.jbzd.com.pl/mikroblog/user/profile/{user_id}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 404:
            print(f"Worker {worker_id} - 404: {user_id}")
            return user_id
    except requests.RequestException:
        pass
    time.sleep(delay_between_requests)
    return None

all_ids = range(chunk_start, chunk_end + 1)
results = []

with ThreadPoolExecutor(max_workers=threads) as executor:
    future_to_id = {executor.submit(check_id, uid): uid for uid in all_ids}
    for future in as_completed(future_to_id):
        res = future.result()
        if res is not None:
            results.append(res)

# Zapis wyników do pliku
with open(filename, "w") as f:
    for user_id in sorted(results):
        f.write(f"{user_id}\n")

print(f"Worker {worker_id} zakończył. Wyniki zapisane w {filename}")
