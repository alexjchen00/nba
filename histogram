import pandas as pd
import matplotlib.pyplot as plt
import math, random, time

# Path to the CSV you uploaded
csv_path = "nba_active_players_ages_2025-06-16.csv"
df = pd.read_csv(csv_path)

# Auto-detect the age column
age_col = next(c for c in df.columns if "age" in c.lower())

# Convert to whole-year ages
if "day" in age_col.lower():
    ages = (df[age_col] / 365.25).apply(math.floor)
else:
    ages = pd.to_numeric(df[age_col], errors="coerce").dropna().astype(int)

num_players = ages.count()
min_age, max_age = ages.min(), ages.max()
bins = range(min_age, max_age + 2)   # one bin per single-year age

plt.figure(figsize=(9, 5))
plt.hist(ages, bins=bins,
         color="#ff6a00",   # red with a tinge of yellow
         edgecolor="black")
plt.title(f"NBA Player Ages Histogram – 2024-25 Season (N={num_players})")
plt.xlabel("Age (years)")
plt.ylabel("Number of Players")
plt.xticks(range(min_age, max_age + 1))
plt.tight_layout()
plt.show()
