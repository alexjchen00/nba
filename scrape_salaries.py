#!/usr/bin/env python3
"""
Scrape 2024-25 NBA salaries (contracts pages) – dynamic column ID
Shows raw cell text for every player, keeps only rows with digits.
"""

import csv, time, random, re, unicodedata, requests
from bs4 import BeautifulSoup, Comment

OUTFILE   = "nba_salary_2024_25.csv"
CON_URL   = "https://www.basketball-reference.com/contracts/{}.html"
HEADERS   = {"User-Agent": "Mozilla/5.0 (Chrome/124 Safari/537.36)"}

TEAMS = {
    "ATL":"Atlanta Hawks","BOS":"Boston Celtics","BRK":"Brooklyn Nets",
    "CHA":"Charlotte Hornets","CHI":"Chicago Bulls","CLE":"Cleveland Cavaliers",
    "DAL":"Dallas Mavericks","DEN":"Denver Nuggets","DET":"Detroit Pistons",
    "GSW":"Golden State Warriors","HOU":"Houston Rockets","IND":"Indiana Pacers",
    "LAC":"Los Angeles Clippers","LAL":"Los Angeles Lakers","MEM":"Memphis Grizzlies",
    "MIA":"Miami Heat","MIL":"Milwaukee Bucks","MIN":"Minnesota Timberwolves",
    "NOP":"New Orleans Pelicans","NYK":"New York Knicks","OKC":"Oklahoma City Thunder",
    "ORL":"Orlando Magic","PHI":"Philadelphia 76ers","PHO":"Phoenix Suns",
    "POR":"Portland Trail Blazers","SAC":"Sacramento Kings","SAS":"San Antonio Spurs",
    "TOR":"Toronto Raptors","UTA":"Utah Jazz","WAS":"Washington Wizards",
}
CON_FIX = {"CHA": "CHO"}

digits_only = re.compile(r"[^\d]")
clean = lambda s: re.sub(r"[^\w\s]","",
                         unicodedata.normalize("NFKD",s)
                                   .encode("ascii","ignore").decode()).lower().strip()

def polite_get(url):
    time.sleep(1.2 + random.random()*0.3)
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def expand(html):
    soup,q = BeautifulSoup(html,"lxml"), []
    q.append(soup)
    while q:
        s=q.pop()
        for n in s.find_all(string=lambda t:isinstance(t,Comment) and "<table" in t):
            c=BeautifulSoup(n,"lxml")
            n.replace_with(c); q.append(c)
    return soup

rows=[]
for abbr, full in TEAMS.items():
    url_abbr = CON_FIX.get(abbr, abbr)
    print(f"\n▶ {abbr}  {full}")
    soup = expand(polite_get(CON_URL.format(url_abbr)))

    # find the header cell that literally shows "2024-25"
    hdr = soup.select_one('th:contains("2024-25")')
    if not hdr:
        print("   ⚠ 2024-25 column not found, skipping team")
        continue
    col_id = hdr["data-stat"]           # e.g. "y1"

    start = len(rows)
    for tr in soup.select("table tbody tr"):
        if "thead" in tr.get("class", []): continue
        link = tr.select_one('[data-stat="player"] a')
        if not link: continue

        sal_td = tr.select_one(f'td[data-stat="{col_id}"]')
        raw = sal_td.text.strip() if sal_td else ""
        print(f"   {link.text:<22} raw → “{raw}”")

        if not any(ch.isdigit() for ch in raw):
            continue                    # dash or blank

        salary = int(digits_only.sub("", raw))
        rows.append([clean(link.text), full, salary])

    added = len(rows) - start
    print(f"   ✔ kept {added} rows (running total {len(rows)})")
    input("Press ↵ for next team … ")

# write CSV
rows.sort(key=lambda r: (r[1], r[0]))
with open(OUTFILE,"w",newline="",encoding="utf-8") as f:
    csv.writer(f).writerows(
        [["name_key","team","salary_2024_25"]] + rows
    )

print(f"\n✅ wrote {len(rows)} rows → {OUTFILE}")
