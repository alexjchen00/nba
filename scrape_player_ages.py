import csv, datetime as dt, math, requests, time

AS_OF = dt.date(2025, 6, 16)
OUT   = "nba_active_players_ages_2025-06-16.csv"

def pages(url):
    page = 1
    while True:
        j = requests.get(url, params={"page": page, "per_page": 100}).json()
        yield from j["data"]
        if page >= j["meta"]["total_pages"]:
            break
        page += 1
        time.sleep(0.1)          # keep it polite

ids = {s["player_id"] for s in requests.get(
        "https://www.balldontlie.io/api/v1/season_averages",
        params={"season": 2024, "per_page": 1000}).json()["data"]}

rows = []
for p in pages("https://www.balldontlie.io/api/v1/players"):
    if p["id"] not in ids:        # skips retired/two-way who never logged a minute
        continue
    dob = dt.date.fromisoformat(p["date_of_birth"])
    age_days  = (AS_OF - dob).days
    age_years = math.floor(age_days / 365.2425)
    rows.append([
        p["id"], p["first_name"], p["last_name"],
        p["team"]["full_name"], dob.isoformat(),
        age_years, age_days
    ])

rows.sort(key=lambda r: (r[3], r[2], r[1]))    # team, last, first

with open(OUT, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(
        [["player_id","first_name","last_name","team","dob","age_years","age_days"]]+rows)

print(f"✅  Wrote {len(rows)} rows → {OUT}")
