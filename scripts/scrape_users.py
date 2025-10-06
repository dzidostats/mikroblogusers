import json
import requests
from concurrent.futures import ThreadPoolExecutor
import argparse
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("--job-index", type=int, required=True)
parser.add_argument("--total-jobs", type=int, required=True)
parser.add_argument("--concurrency", type=int, default=5)
parser.add_argument("--output", type=str, required=True)
args = parser.parse_args()

with open("results/all_names.json", encoding="utf-8") as f:
    all_users = json.load(f)

total_users = len(all_users)
chunk_size = total_users // args.total_jobs
start = (args.job_index - 1) * chunk_size
end = start + chunk_size if args.job_index < args.total_jobs else total_users
users_chunk = all_users[start:end]

results = []

def fetch_user(username):
    url = f"https://jbzd.com.pl/search/users?page=1&per_page=10000&phrase={username}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"username": username, "error": f"status {resp.status_code}"}
    except Exception as e:
        return {"username": username, "error": str(e)}

with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
    for res in tqdm(executor.map(fetch_user, users_chunk), total=len(users_chunk)):
        results.append(res)

with open(args.output, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
