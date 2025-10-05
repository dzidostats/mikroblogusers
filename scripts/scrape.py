import aiohttp
import asyncio
import json
import sys

start_id = int(sys.argv[1])
end_id = int(sys.argv[2])
output_file = sys.argv[3]
failed_file = sys.argv[4]

MAX_RETRIES = 3
CONCURRENCY = 5
TIMEOUT = 5

names = []
failed_ids = []

semaphore = asyncio.Semaphore(CONCURRENCY)

async def fetch_user(session, user_id):
    url = f"https://jbzd.com.pl/mikroblog/user/profile/{user_id}"
    for attempt in range(1, MAX_RETRIES + 1):
        async with semaphore:
            try:
                async with session.get(url, timeout=TIMEOUT) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "user" in data and "name" in data["user"]:
                            return data["user"]["name"]
                        return None
                    elif resp.status == 404:
                        return None
                    elif resp.status == 429:
                        print(f"[RATE LIMIT] ID {user_id} – czekam 10s")
                        await asyncio.sleep(10)
                    else:
                        print(f"[WARN] ID {user_id} → HTTP {resp.status} (próba {attempt}/{MAX_RETRIES})")
                        await asyncio.sleep(1)
            except Exception as e:
                print(f"[ERROR] ID {user_id}: {type(e).__name__} ({e}), próba {attempt}/{MAX_RETRIES}")
                await asyncio.sleep(1)
    failed_ids.append(user_id)
    return None


async def main():
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [fetch_user(session, uid) for uid in range(start_id, end_id + 1)]
        results = await asyncio.gather(*tasks)

    for name in results:
        if name:
            names.append(name)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(names, f, ensure_ascii=False, indent=2)

    with open(failed_file, "w", encoding="utf-8") as f:
        json.dump(failed_ids, f, ensure_ascii=False, indent=2)

    print(f"✅ Zapisano {len(names)} nazw, ⚠️ {len(failed_ids)} błędów")


if __name__ == "__main__":
    asyncio.run(main())
