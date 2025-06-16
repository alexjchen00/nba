#!/usr/bin/env python3
"""
NBA 2024-25 snapshot — AGE ONLY
(as of 16-Jun-2025)

Output → nba_player_ages_2025-06-16.csv
"""

import csv, datetime as dt, random, re, time, unicodedata, requests
from bs4 import BeautifulSoup, Comment

# ───────────────── CONFIG ─────────────────
AS_OF      = dt.date(2025, 6, 16)
HEADERS    = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Referer"   : "https://www.basketball-reference.com/"
}
BASE_ROSTER = "https://www.basketball-reference.com/teams/{}/2025.html"
OUTFILE     = "nba_player_ages_2025-06-16.csv"

TEAMS = [
    "ATL","BOS","BRK","CHA","CHI","CLE","DAL","DEN","DET","GSW",
    "HOU","IND","LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK",
    "OKC","ORL","PHI","PHO","POR","SAC","SAS","TOR","UTA","WAS"
]
TEAM_NAMES = { t: n for t, n in zip(
    TEAMS,
    ["Atlanta Hawks","Boston Celtics","Brooklyn Nets","Charlotte Hornets",
     "Chicago Bulls","Cleveland Cavaliers","Dallas Mavericks","Denver Nuggets",
     "Detroit Pistons","Golden State Warriors","Houston Rockets","Indiana Pacers",
     "Los Angeles Clippers","Los Angeles Lakers","Memphis Grizzlies","Miami Heat",
     "Milwaukee Bucks","Minnesota Timberwolves","New Orleans Pelicans",
     "New York Knicks","Oklahoma City Thunder","Orlando Magic",
     "Philadelphia 76ers","Phoenix Suns","Portland Trail Blazers",
     "Sacramento Kings","San Antonio Spurs","Toronto Raptors",
     "Utah Jazz","Washington Wizards"]) }

parse_date  = lambda s: dt.datetime.strptime(s, "%Y%m%d").date()

# ───────── polite fetch w/ jitter ─────────
def polite_get(url, base_delay=1.1):
    time.sleep(base_delay + random.random()*0.4)   # 1.1-1.5 s per hit
    return requests.get(url, headers=HEADERS, timeout=20)

# ───────── expand nested comment markup ─────────
def unwrap_comments(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "lxml")
    queue = [soup]
    while queue:
        s = queue.pop(0)
        for node in s.find_all(string=lambda t: isinstance(t, Comment) and "<table" in t):
            child = BeautifulSoup(node, "lxml")
            node.replace_with(child)
            queue.append(child)
    return soup

# ───────── scrape ages ─────────
rows = []
print("\nFetching 30 roster pages (≈ 35 s)…\n")
for abbr in TEAMS:
    soup = unwrap_comments(polite_get(BASE_ROSTER.format(abbr)).text)
    team = TEAM_NAMES[abbr]

    for tr in soup.select("table tbody tr"):
        link   = tr.select_one('[data-stat="player"] a')      # works for <th> & <td>
        dob_td = tr.select_one('td[data-stat="birth_date"]')
        yrs_td = tr.select_one('td[data-stat="years_experience"]')
        if not (link and dob_td and "csk" in dob_td.attrs):
            continue                                          # skip: no DOB
        name = link.text.strip()
        dob  = parse_date(dob_td["csk"])
        yrs_raw   = yrs_td.text.strip()
        years_exp = 0 if yrs_raw in ("R","") else int(yrs_raw)
        age_days  = (AS_OF - dob).days

        rows.append([name, team, dob.isoformat(), years_exp, age_days])

    print(" ", abbr, "done")

rows.sort(key=lambda r: (r[1], r[0]))        # team, then name

# ───────── write CSV ─────────
with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(
        [["name","team","dob","years_exp","age_days"]] + rows
    )

print(f"\n✅ wrote {len(rows)} rows → {OUTFILE}")
