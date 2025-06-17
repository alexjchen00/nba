#!/usr/bin/env python3
"""
Super-plot: Average & Median Salary + Average & Median Total Points
per exact age (one bin per age), overlaid with the same dashed
cumulative-salary line.  Uses the merged file produced earlier.
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import math
import unicodedata, re

MERGED_CSV = "nba_ages_pts_salary_2025.csv"   # adjust path if needed

# ── helper to normalise names if re-merging later ──────────────────────────
clean = lambda s: re.sub(r"[^\w\s]", "",
                         unicodedata.normalize("NFKD", s)
                                   .encode("ascii","ignore").decode()).lower().strip()

# ── load & prep ────────────────────────────────────────────────────────────
df = pd.read_csv(MERGED_CSV)

# ensure an integer-age column
if "age_years" not in df.columns:
    if "age_days" in df.columns:
        df["age_years"] = (df["age_days"] / 365.25).apply(math.floor)
    else:
        raise ValueError("Need age_days or age_years in merged file.")

# numeric salary & points
df["salary"] = pd.to_numeric(df["salary"], errors="coerce").fillna(0).astype(int)
pts_col = "total_points" if "total_points" in df.columns else "pts_2024_25"
df[pts_col] = pd.to_numeric(df[pts_col], errors="coerce").fillna(0).astype(int)

# group by age
grp   = df.groupby("age_years")
ages  = grp.size().index.astype(int).sort_values()

avg_sal = grp["salary"].mean().loc[ages]
med_sal = grp["salary"].median().loc[ages]

avg_pts = grp[pts_col].mean().loc[ages]
med_pts = grp[pts_col].median().loc[ages]

# cumulative share of total salary (same for all panels)
cum_pct_sal = grp["salary"].sum().loc[ages].cumsum() \
              / grp["salary"].sum().loc[ages].sum() * 100

# formatters
dollar_fmt = FuncFormatter(lambda x, _ : f"${x/1e6:,.1f}M")
comma_fmt  = FuncFormatter(lambda x, _ : f"{int(x):,}")

blue  = "#1f77b4"
teal  = "#009e9e"

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
(ax_avg_sal, ax_med_sal), (ax_avg_pts, ax_med_pts) = axes

def bar_panel(ax, series, color, y_fmt, title, ylab):
    ax.bar(ages, series.loc[ages], edgecolor="black", align="center",
           color=color)
    ax.set_xticks(ages)
    ax.set_xlabel("Age (years)")
    ax.set_ylabel(ylab)
    ax.set_title(title)
    ax.yaxis.set_major_formatter(y_fmt)

    ax2 = ax.twinx()
    ax2.plot(ages, cum_pct_sal, linestyle="--", color="red")
    ax2.set_ylabel("Cumulative % of Total Salary", color="red")
    ax2.set_ylim(0, 100)
    ax2.tick_params(axis='y', colors='red')

bar_panel(ax_avg_sal, avg_sal, blue,  dollar_fmt,
          "Average Salary by Age – 2024-25 (N=518)", "Average Salary")

bar_panel(ax_med_sal, med_sal, blue,  dollar_fmt,
          "Median Salary by Age – 2024-25 (N=518)",  "Median Salary")

bar_panel(ax_avg_pts, avg_pts, teal,  comma_fmt,
          "Average Total Points by Age – 2024-25 (N=518)", "Average Points")

bar_panel(ax_med_pts, med_pts, teal,  comma_fmt,
          "Median Total Points by Age – 2024-25 (N=518)",  "Median Points")

plt.tight_layout()
plt.show()
