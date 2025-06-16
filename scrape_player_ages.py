import csv, datetime as dt, math, time, requests

AS_OF = dt.date(2025, 6, 16)
OUT   = "nba_active_players_ages_2025-06-16.csv"
HEAD  = {"User-Agent": "Mozilla/5.0"}      # some CDNs block python default UA

def pages(endpoint):
    page = 1
    while True:
        r = requests.get(endpoint,
                         params={"page": page, "per_page": 100},
                         headers=HEAD, timeout=10)
        if r.status_code != 200:
            raise RuntimeError(f"{endpoint} page {page} → {r.status_code}")
        yield from r.json()["data"]
        if page >= r.json()["meta"]["total_pages"]:
            break
        page += 1
        time.sleep(0.25)           # stay under rate limit

# Build a set of player IDs who logged minutes in 2024-25
ids = set()
for p in pages("https://www.balldontlie.io/api/v1/players"):
    if p["team"] is not None:      # filters out retired + gleague nowhere guys
        ids.add(p["id"])

rows = []
for p in pages("https://www.balldontlie.io/api/v1/players"):
    if p["id"] not in ids:
        continue
    dob = dt.date.fromisoformat(p["date_of_birth"])
    age_days  = (AS_OF - dob).days
    age_years = math.floor(age_days / 365.2425)
    rows.append([p["id"], p["first_name"], p["last_name"],
                 p["team"]["full_name"], dob.isoformat(),
                 age_years, age_days])

rows.sort(key=lambda r: (r[3], r[2], r[1]))
with open(OUT, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(
        [["player_id","first_name","last_name","team",
          "dob","age_years","age_days"]]+rows)

print(f"✅ wrote {len(rows)} rows to {OUT}")
