import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

start_id = 1
end_id = 100_000
max_workers = 2  # liczba workerów
delay_between_requests = 0.05

# Lock do synchronizacji numeru workera
worker_lock = threading.Lock()
worker_count = 0

def get_worker_file():
    global worker_count
    with worker_lock:
        worker_count += 1
        return f"404_ids_worker_{worker_count}.txt"

def check_id_range(worker_id, id_range):
    filename = f"404_ids_worker_{worker_id}.txt"
    with open(filename, "w") as f:
        for user_id in id_range:
            url = f"https://m.jbzd.com.pl/mikroblog/user/profile/{user_id}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 404:
                    print(f"Worker {worker_id} - 404: {user_id}")
                    f.write(f"{user_id}\n")
            except requests.RequestException:
                pass
            time.sleep(delay_between_requests)

# Podział zakresu ID na bloki dla workerów
def chunk_range(start, end, chunks):
    total = end - start + 1
    chunk_size = total // chunks
    ranges = []
    for i in range(chunks):
        chunk_start = start + i * chunk_size
        chunk_end = start + (i + 1) * chunk_size - 1 if i < chunks - 1 else end
        ranges.append(range(chunk_start, chunk_end + 1))
    return ranges

# Start wątków
id_ranges = chunk_range(start_id, end_id, max_workers)
threads = []

for i, r in enumerate(id_ranges, start=1):
    t = threading.Thread(target=check_id_range, args=(i, r))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print("Gotowe! Każdy worker zapisał swoje ID 404 w osobnym pliku.")
