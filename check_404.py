# plik: check_404.py
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

output_file = "404_ids.txt"

def check_id(user_id):
    url = f"https://m.jbzd.com.pl/mikroblog/user/profile/{user_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 404:
            return user_id
    except requests.RequestException:
        return None
    return None

start_id = 1
end_id = 100_000
max_workers = 2  # 2 wątki
delay_between_requests = 0.05

with open(output_file, "w") as f, ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = {executor.submit(check_id, i): i for i in range(start_id, end_id + 1)}

    for future in as_completed(futures):
        user_id = future.result()
        if user_id is not None:
            print(f"404: {user_id}")
            f.write(f"{user_id}\n")
        time.sleep(delay_between_requests)

print(f"Gotowe! Wyniki zapisane w {output_file}.")
