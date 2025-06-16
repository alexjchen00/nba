import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math, random, time

# 1. Load your ages CSV
csv_path = "nba_active_players_ages_2025-06-16.csv"
df = pd.read_csv(csv_path)

# 2. Auto-detect the age column
age_col = next(c for c in df.columns if "age" in c.lower())

# 3. Convert to whole-year ages
if "day" in age_col.lower():                 # if you have age in days
    ages = (df[age_col] / 365.25).apply(math.floor)
else:                                        # already in years
    ages = pd.to_numeric(df[age_col], errors="coerce").dropna().astype(int)

num_players = ages.count()                   # N for title
min_age, max_age = ages.min(), ages.max()
bins = np.arange(min_age, max_age + 2)       # one bin per integer age

# 4. Histogram counts
hist_counts, _ = np.histogram(ages, bins=bins)

# 5. Cumulative percentile
cum_counts  = np.cumsum(hist_counts)
cum_percent = cum_counts / num_players * 100  # 0–100 %

# 6. Plot
fig, ax1 = plt.subplots(figsize=(9, 5))

# Histogram bars (red-orange fill, black edges)
ax1.bar(
    bins[:-1], hist_counts, width=0.8,
    color="#ff6a00", edgecolor="black", align="edge"
)
ax1.set_xlabel("Age (years)")
ax1.set_ylabel("Number of Players")
ax1.set_xticks(bins[:-1])
ax1.set_title(f"NBA Player Ages Histogram – 2024-25 Season (N={num_players})")

# Secondary axis: cumulative percentile
ax2 = ax1.twinx()
ax2.plot(
    bins[:-1] + 0.4,      # center the line on each bar
    cum_percent,
    color="red", linestyle="--"
)
ax2.set_ylabel("Cumulative Percentile (%)", color="red")
ax2.set_ylim(0, 100)
ax2.tick_params(axis="y", colors="red")

plt.tight_layout()
plt.show()
