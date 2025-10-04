import json
import sys
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import uniform

def get_name(user_id):
    url = f"https://jbzd.com.pl/mikroblog/user/profile/{user_id}"
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        name_tag = soup.find("h1", class_="profile__name")
        if not name_tag:
            return None
        return name_tag.text.strip()
    except Exception:
        return None

def main():
    if len(sys.argv) != 3:
        print("Usage: python scraper.py start_id end_id")
        sys.exit(1)

    start_id = int(sys.argv[1])
    end_id = int(sys.argv[2])
    data = {}

    for uid in range(start_id, end_id + 1):
        name = get_name(uid)
        if name:
            data[uid] = name
        sleep(uniform(0.5, 1.5))

    filename = f"jbzd_users_{start_id}_{end_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} users to {filename}")

if __name__ == "__main__":
    main()
