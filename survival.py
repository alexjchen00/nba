import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================================
# One‑stop script: NBA career‑longevity plots
# Key = Player_additional  (name + birth‑year)
# Cohort: careers starting 1995‑to‑present
# Censor: careers still active in 2024+
# =========================================

START_YEAR   = 1995     # cohort lower bound
CENSOR_YEAR  = 2024     # right‑censor threshold
ROLL_WINDOW  = 5        # running‑avg window for churn plot

# ---------- Load & prep ----------
df = pd.read_csv('/mnt/data/nba_per_game_1990_2025.csv').dropna(subset=['Age'])
df['birth_year'] = (df['Year'] - df['Age']).astype(int)
df['Player_additional'] = df['Player'] + '_' + df['birth_year'].astype(str)

# One row per player‑season (drop per‑team duplicates)
df = df.drop_duplicates(subset=['Year', 'Player_additional'])

# ---------- 1. Roster Churn % ----------
last_seen = df.groupby('Player_additional')['Year'].max()
df['IsExit'] = df.apply(lambda r: r['Year'] == last_seen[r['Player_additional']], axis=1)
seasons = list(range(START_YEAR, CENSOR_YEAR))
churn_pct = (df[df['Year'].isin(seasons)]
             .groupby('Year')['IsExit']
             .mean() * 100)
churn_roll = churn_pct.rolling(window=ROLL_WINDOW, center=True, min_periods=3).mean()

plt.figure(figsize=(9,5))
plt.step(churn_pct.index, churn_pct, where='mid', marker='o', label='Annual churn')
plt.plot(churn_roll.index, churn_roll, lw=2.5, label=f'{ROLL_WINDOW}-yr avg')
plt.title('NBA Roster Churn — Final‑Season Players (1995‑2023)')
plt.xlabel('Season')
plt.ylabel('Share of Players (%)')
plt.grid(True, ls='--', lw=0.5)
plt.legend()
plt.tight_layout()
plt.show()

# ---------- 2. Career‑Length Box Plot ----------
career = (df.groupby('Player_additional')['Year']
            .agg(first='min', seasons='nunique')
            .reset_index())
lengths = career[career['first'] >= START_YEAR]['seasons']

plt.figure(figsize=(8,4))
plt.boxplot(lengths, vert=False, patch_artist=True, showfliers=True)
plt.title('Distribution of NBA Career Lengths (Starts 1995‑2025)')
plt.xlabel('Career Length (seasons)')
plt.tight_layout()
plt.show()

# ---------- 3. ECDF ----------
lengths_sorted = np.sort(lengths)
cdf = np.arange(1, len(lengths_sorted)+1) / len(lengths_sorted) * 100

plt.figure(figsize=(9,5))
plt.step(lengths_sorted, cdf, where='post', lw=2)
plt.title('Cumulative Percentile of NBA Career Lengths (Starts 1995‑2025)')
plt.xlabel('Career Length (seasons)')
plt.ylabel('Players ≤ length (%)')
plt.xticks(range(1, lengths_sorted.max()+1))
for p in [25, 50, 75, 90, 99]:
    idx = np.argmax(cdf >= p)
    x, y = lengths_sorted[idx], cdf[idx]
    plt.scatter(x, y, zorder=3)
    plt.text(x+0.2, y-2, f'{p}th → {x}', va='top', fontsize=9)
plt.grid(True, ls='--', lw=0.5, alpha=0.7)
plt.tight_layout()
plt.show()

# ---------- 4. Kaplan–Meier Survival Curve ----------
career['last']  = df.groupby('Player_additional')['Year'].max().values
career['event'] = (career['last'] < CENSOR_YEAR).astype(int)
km = career[career['first'] >= START_YEAR]

durations = km['seasons'].values
events    = km['event'].values
event_times = np.sort(km.loc[events==1, 'seasons'].unique())

surv = 1.0
times, surv_vals = [0], [100]
for t in event_times:
    at_risk = np.sum(durations >= t)
    d       = np.sum((durations == t) & (events == 1))
    surv *= (1 - d / at_risk)
    times.extend([t, t])
    surv_vals.extend([surv_vals[-1], surv*100])
times.append(25); surv_vals.append(surv_vals[-1])

median_len = next(t for t, s in zip(event_times, surv_vals[2::2]) if s <= 50)

plt.figure(figsize=(10,5))
plt.step(times, surv_vals, where='post', lw=2)
plt.axhline(50, color='gray', ls='--', lw=1)
plt.axvline(median_len, color='gray', ls='--', lw=1)
plt.scatter([median_len],[50], zorder=3)
plt.text(median_len+0.3, 52, f'Median: {median_len} seasons', va='bottom')
plt.title('NBA Career Survival Curve (Starts 1995‑2025)')
plt.xlabel('Career Length (seasons)')
plt.ylabel('Survival Probability (%)')
plt.xlim(0, 25)
plt.xticks(range(0,26,1))
plt.ylim(0, 105)
plt.grid(True, ls='--', lw=0.5, alpha=0.7)
plt.tight_layout()
plt.show()
