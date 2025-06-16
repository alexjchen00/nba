#!/usr/bin/env python3
"""
NBA 2024-25 snapshot — total points, age, salary
(as of 16 Jun 2025)

Outputs: nba_pts_age_salary_2025-06-16.csv
"""

import csv, datetime as dt, random, re, time, requests, sys
from bs4 import BeautifulSoup, Comment

# ───────────────────────────── CONFIG ──────────────────────────────
AS_OF       = dt.date(2025, 6, 16)
SAL_COL     = "y2025"                       # 2024-25 salary column
HEADERS     = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Referer": "https://www.basketball-reference.com/"
}
TOTALS_URL  = "https://www.basketball-reference.com/leagues/NBA_2025_totals.html"
BASE_ROSTER = "https://www.basketball-reference.com/teams/{}/2025.html"
BASE_CONT   = "https://www.basketball-reference.com/contracts/{}.html"
OUTFILE     = "nba_pts_age_salary_2025-06-16.csv"

TEAMS = [
    "ATL","BOS","BRK","CHA","CHI","CLE","DAL","DEN","DET","GSW",
    "HOU","IND","LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK",
    "OKC","ORL","PHI","PHO","POR","SAC","SAS","TOR","UTA","WAS"
]

TEAM_NAMES = { t: n for t, n in zip(TEAMS,
    ["Atlanta Hawks","Boston Celtics","Brooklyn Nets","Charlotte Hornets",
     "Chicago Bulls","Cleveland Cavaliers","Dallas Mavericks","Denver Nuggets",
     "Detroit Pistons","Golden State Warriors","Houston Rockets","Indiana Pacers",
     "Los Angeles Clippers","Los Angeles Lakers","Memphis Grizzlies","Miami Heat",
     "Milwaukee Bucks","Minnesota Timberwolves","New Orleans Pelicans",
     "New York Knicks","Oklahoma City Thunder","Orlando Magic",
     "Philadelphia 76ers","Phoenix Suns","Portland Trail Blazers",
     "Sacramento Kings","San Antonio Spurs","Toronto Raptors",
     "Utah Jazz","Washington Wizards"] )
}

digits_only = re.compile(r"[^\d]")
parse_date  = lambda s: dt.datetime.strptime(s, "%Y%m%d").date()

# ────────────────────── polite fetch with back-off ──────────────────────
def get_with_backoff(url, *, max_retries=8, base_delay=1.2):
    delay = base_delay
    for _ in range(max_retries):
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code not in (429, 503):
            return r
        print(f"  {url.split('/')[-1]} → {r.status_code}, sleep {delay:.1f}s")
        time.sleep(delay + random.uniform(0, delay * 0.3))
        delay = min(delay * 2, 30)
    raise RuntimeError(f"Gave up on {url}")

# ─────────────────────── unwrap nested comment markup ───────────────────
def unwrap_comments(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "lxml")
    queue = [soup]
    while queue:
        s = queue.pop(0)
        for c in s.find_all(string=lambda t: isinstance(t, Comment)):
            child = BeautifulSoup(c, "lxml")
            c.replace_with(child)
            queue.append(child)
    return soup

# ───────────────────── 1️⃣  TOTAL POINTS (PTS) ─────────────────────
print("Fetching totals page…")
totals_html = get_with_backoff(TOTALS_URL).text
tot_soup    = unwrap_comments(totals_html)

# pick the first table that has both player & pts columns
tot_table = next(tbl for tbl in tot_soup.find_all("table")
                 if tbl.select_one('td[data-stat="player"]')
                 and tbl.select_one('td[data-stat="pts"]'))

points = {}   # pid → total points
for tr in tot_table.select("tbody tr"):
    link = tr.select_one('td[data-stat="player"] a')
    if not link:
        continue
    pid = link["href"].split("/")[-1].replace(".html", "")
    pts_raw = tr.select_one('td[data-stat="pts"]').text.strip()
    points[pid] = int(pts_raw) if pts_raw else 0
print(f"  grabbed {len(points)} point totals\n")

# ───────────────────── 2️⃣  SALARIES ─────────────────────
salary = {}
print("Fetching contracts pages…")
for abbr in TEAMS:
    html = unwrap_comments(get_with_backoff(BASE_CONT.format(abbr)).text)
    for tr in html.select("table tbody tr"):
        link = tr.select_one('[data-stat="player"] a')
        if not link:
            continue
        pid = link["href"].split("/")[-1].replace(".html", "")
        sal_raw = digits_only.sub("",
                  tr.select_one(f'td[data-stat="{SAL_COL}"]').text)
        salary[pid] = int(sal_raw) if sal_raw else 0
    time.sleep(1.0 + random.random()*0.4)   # ~1-1.4 s per page
print(f"  grabbed {len(salary)} salary rows\n")

# ───────────────────── 3️⃣  ROSTERS (DOB & years) ─────────────────────
rows = []
print("Fetching roster pages…")
for abbr in TEAMS:
    html = unwrap_comments(get_with_backoff(BASE_ROSTER.format(abbr)).text)
    team = TEAM_NAMES[abbr]

    for tr in html.select("table tbody tr"):
        link   = tr.select_one('[data-stat="player"] a')
        dob_td = tr.select_one('td[data-stat="birth_date"]')
        yrs_td = tr.select_one('td[data-stat="years_experience"]')
        if not (link and dob_td and "csk" in dob_td.attrs):
            continue
        pid  = link["href"].split("/")[-1].replace(".html", "")
        if pid not in points:             # never played → skip
            continue
        name = link.text.strip()
        dob  = parse_date(dob_td["csk"])
        yrs_raw = yrs_td.text.strip()
        years   = 0 if yrs_raw in ("R","") else int(yrs_raw)
        age_days = (AS_OF - dob).days
        sal = salary.get(pid, 0)
        pts = points[pid]

        rows.append([pid, name, team, dob.isoformat(),
                     years, age_days, pts, sal])
    time.sleep(1.0 + random.random()*0.4)
print(f"  kept {len(rows)} players with DOB\n")

# ───────────────────── 4️⃣  OUTPUT CSV ─────────────────────
rows.sort(key=lambda r: (r[2], r[1]))      # team, then name
with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(
        [["player_id","name","team","dob",
          "years_exp","age_days","pts_2024_25","salary_2024_25"]] + rows
    )

print(f"✅ wrote {len(rows)} rows → {OUTFILE}")
