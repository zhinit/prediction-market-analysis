"""Export all plots from mlb_calibration notebook to write_ups/images/."""
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import polars as pl

IMAGES = Path(__file__).parent / "images"
IMAGES.mkdir(exist_ok=True)

# ── DB ──
con = duckdb.connect(Path(__file__).parent / "../db/pma.db", read_only=True)
con.sql("""
    CREATE OR REPLACE TEMP VIEW pre_home AS
    SELECT * FROM mlb_calib_pre_snapshots WHERE side = 'home'
""")

# ── Style ──
GREEN = "#3d7356"
CLAY = "#c2703d"
INK = "#1c1c1a"
MUTED = "#6e6e6c"
GRID = "#ededeb"
BASELINE = "#d9d9d7"
SURFACE = "#fafaf8"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": BASELINE,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.labelcolor": MUTED,
    "text.color": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlelocation": "left",
    "figure.dpi": 150,
})

# ── Stats helpers ──
def wilson(p_hat, n, z=1.96):
    p_hat = np.asarray(p_hat, dtype=float)
    n = np.asarray(n, dtype=float)
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denom
    return center - half, center + half


def with_deviation(df):
    lo, hi = wilson(df["win_rate"].to_numpy(), df["n_samples"].to_numpy())
    return df.with_columns(
        pl.Series("ci_lo", lo),
        pl.Series("ci_hi", hi),
        (pl.col("win_rate") - pl.col("avg_price")).alias("deviation"),
        (pl.Series(lo) - pl.col("avg_price")).alias("dev_lo"),
        (pl.Series(hi) - pl.col("avg_price")).alias("dev_hi"),
    )


# ── Query helpers ──
def calibration(rel="pre_home", where="TRUE", buckets=10, params=None):
    df = con.execute(f"""
        SELECT least(floor(p * {buckets}), {buckets - 1})::INT AS bucket,
               avg(p) AS avg_price,
               avg(y) AS win_rate,
               count(*) AS n_samples
        FROM {rel}
        WHERE {where}
        GROUP BY bucket ORDER BY bucket
    """, params).pl()
    return with_deviation(df)


def group_deviation(rel, expr, where="TRUE", order_by="grp"):
    df = con.sql(f"""
        SELECT {expr} AS grp,
               count(*) AS n_samples,
               avg(p) AS avg_price,
               avg(y) AS win_rate
        FROM {rel}
        WHERE {where}
        GROUP BY grp ORDER BY {order_by}
    """).pl()
    return with_deviation(df)


# ── Plot helpers ──
def plot_calibration(ax, df, color=GREEN, label=None):
    ax.plot([0, 1], [0, 1], ls="--", lw=1, color=BASELINE, zorder=1)
    x = df["avg_price"].to_numpy()
    y = df["win_rate"].to_numpy()
    yerr = np.vstack([y - df["ci_lo"].to_numpy(),
                      df["ci_hi"].to_numpy() - y])
    ax.errorbar(x, y, yerr=yerr, fmt="o-", ms=3.5, lw=1.5, color=color,
                elinewidth=1, capsize=2, label=label, zorder=3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")


PCT = mtick.PercentFormatter(xmax=1, decimals=0)
CENTS = mtick.FuncFormatter(lambda p, _: f"{p * 100:.0f}¢")


def save(fig, name):
    fig.savefig(IMAGES / name, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"  saved {name}")


# ── 1. Overall calibration ──
print("1. Overall calibration")
overall = calibration()

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1, 1.3]})

plot_calibration(ax1, overall)
ax1.set_xlabel("pre-game price (implied probability)")
ax1.set_ylabel("share of samples resolving YES")
ax1.set_title("Pre-game calibration, 10c buckets", color=INK)
ax1.xaxis.set_major_formatter(CENTS)
ax1.yaxis.set_major_formatter(PCT)

dense = overall.filter(pl.col("n_samples") >= 30)
x = dense["avg_price"].to_numpy()
dev = dense["deviation"].to_numpy()
lo = dense["dev_lo"].to_numpy()
hi = dense["dev_hi"].to_numpy()
ax2.axhline(0, ls="--", lw=1, color=BASELINE, zorder=1)
ax2.fill_between(x, lo, hi, color=GREEN, alpha=0.15, lw=0, zorder=2)
ax2.plot(x, dev, "o-", ms=3.5, lw=1.5, color=GREEN, zorder=3)
ax2.set_xlim(0, 1)
ax2.set_xlabel("pre-game price (implied probability)")
ax2.set_ylabel("win rate − price")
ax2.set_title("Deviation from the diagonal, buckets with ≥30 samples", color=INK)
ax2.xaxis.set_major_formatter(CENTS)
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=1))

fig.tight_layout()
save(fig, "overall-calibration.png")


# ── 2. Calibration by period ──
print("2. Calibration by period")
con.sql("""
    CREATE OR REPLACE TEMP VIEW pre_snap_period AS
    SELECT game_pk, season, p, y, sched_start,
           CASE WHEN sched_start <= median(sched_start)
                    OVER (PARTITION BY season)
                THEN 'early' ELSE 'late' END AS half
    FROM pre_home
""")

PERIODS = [(2025, "early"), (2025, "late"), (2026, "early"), (2026, "late")]

fig, axes = plt.subplots(2, 2, figsize=(8.6, 8.6), sharex=True, sharey=True)
for ax, (season, half) in zip(axes.flat, PERIODS):
    df = calibration("pre_snap_period", "season = ? AND half = ?",
                     buckets=10, params=[season, half])
    plot_calibration(ax, df.filter(pl.col("n_samples") >= 30))
    ax.set_title(f"{season} {half}", color=INK, fontsize=11)
    ax.set_xticks([0, 0.5, 1])
    ax.set_yticks([0, 0.5, 1])
    ax.xaxis.set_major_formatter(CENTS)
    ax.yaxis.set_major_formatter(PCT)

fig.supxlabel("pre-game price (implied probability)", color=MUTED)
fig.supylabel("share of samples resolving YES", color=MUTED)
fig.suptitle("Pre-game calibration by period, 10c buckets (≥30 samples)",
             color=INK, x=0.01, ha="left")
fig.tight_layout()
save(fig, "calibration-by-period.png")


# ── 3. Calibration by inning ──
print("3. Calibration by inning")
INNINGS = (["pre-game"]
           + [f"inning {i}" for i in range(2, 10)]
           + ["extras"])


def inning_calibration(inning, buckets=10):
    if inning == "pre-game":
        return calibration(buckets=buckets)
    if inning == "extras":
        return calibration("mlb_calib_inning_snapshots",
                           "side = 'home' AND entering = 10",
                           buckets=buckets)
    return calibration("mlb_calib_inning_snapshots",
                       "side = 'home' AND entering = ?",
                       buckets=buckets,
                       params=[int(inning.split()[1])])


fig, axes = plt.subplots(3, 4, figsize=(13, 10), sharex=True, sharey=True)
for ax, inning in zip(axes.flat, INNINGS):
    df = inning_calibration(inning)
    plot_calibration(ax, df.filter(pl.col("n_samples") >= 30))
    ax.set_title(inning, color=INK, fontsize=11)
    ax.set_xticks([0, 0.5, 1])
    ax.set_yticks([0, 0.5, 1])
    ax.xaxis.set_major_formatter(CENTS)
    ax.yaxis.set_major_formatter(PCT)

for ax in axes.flat[len(INNINGS):]:
    ax.set_visible(False)
fig.supxlabel("snapshot price (implied probability)", color=MUTED)
fig.supylabel("share of samples resolving YES", color=MUTED)
fig.suptitle("Calibration by inning, 10c buckets (≥30 samples)", color=INK,
             x=0.01, ha="left")
fig.tight_layout()
save(fig, "calibration-by-inning.png")


# ── 4. Home vs away ──
print("4. Home vs away")
fig, ax = plt.subplots(figsize=(6.2, 6.2))

home = calibration("mlb_calib_pre_snapshots", "side = 'home'")
away = calibration("mlb_calib_pre_snapshots", "side = 'away'")
plot_calibration(ax, home.filter(pl.col("n_samples") >= 30),
                 color=GREEN, label="home")
plot_calibration(ax, away.filter(pl.col("n_samples") >= 30),
                 color=CLAY, label="away")

ax.set_xlabel("pre-game price (implied probability)")
ax.set_ylabel("share of samples resolving YES")
ax.set_title("Pre-game calibration by side, 10c buckets (≥30 samples)",
             color=INK)
ax.xaxis.set_major_formatter(CENTS)
ax.yaxis.set_major_formatter(PCT)
ax.legend(loc="upper left", frameon=False)

fig.tight_layout()
save(fig, "calibration-home-away.png")


# ── 5. By team ──
print("5. By team")
teams = (group_deviation("mlb_calib_pre_snapshots", "team")
         .rename({"grp": "team"})
         .sort("deviation", descending=True))

fig, axes = plt.subplots(6, 5, figsize=(13, 16), sharex=True, sharey=True)
for ax, team in zip(axes.flat, teams.sort("team")["team"]):
    df = calibration("mlb_calib_pre_snapshots", "team = ?", buckets=10,
                     params=[team])
    plot_calibration(ax, df.filter(pl.col("n_samples") >= 30))
    ax.set_title(team, color=INK, fontsize=10)
    ax.set_xticks([0, 0.5, 1])
    ax.set_yticks([0, 0.5, 1])
    ax.xaxis.set_major_formatter(CENTS)
    ax.yaxis.set_major_formatter(PCT)

fig.supxlabel("pre-game price (implied probability)", color=MUTED)
fig.supylabel("share of samples resolving YES", color=MUTED)
fig.suptitle("Pre-game calibration by team, 10c buckets (≥30 samples)", color=INK,
             x=0.01, ha="left")
fig.tight_layout()
save(fig, "calibration-by-team.png")


# ── 6a. By weather condition ──
print("6a. By weather condition")
con.sql("""
    CREATE OR REPLACE TEMP VIEW pre_snap_wx AS
    SELECT game_pk, p, y,
           CASE
               WHEN condition IN ('Clear', 'Sunny') THEN 'clear'
               WHEN condition IN ('Partly Cloudy', 'Cloudy', 'Overcast')
                   THEN 'clouds'
               WHEN condition IN ('Roof Closed', 'Dome') THEN 'roof/dome'
               WHEN condition IN ('Rain', 'Drizzle') THEN 'rain'
               ELSE 'other'
           END AS condition_group,
           temp_f,
           wind_mph
    FROM pre_home
""")

fig, axes = plt.subplots(2, 2, figsize=(8.6, 8.6), sharex=True, sharey=True)
for ax, grp in zip(axes.flat, ["clear", "clouds", "roof/dome", "rain"]):
    df = calibration("pre_snap_wx", "condition_group = ?", buckets=10,
                     params=[grp])
    plot_calibration(ax, df.filter(pl.col("n_samples") >= 30))
    ax.set_title(grp, color=INK, fontsize=11)
    ax.set_xticks([0, 0.5, 1])
    ax.set_yticks([0, 0.5, 1])
    ax.xaxis.set_major_formatter(CENTS)
    ax.yaxis.set_major_formatter(PCT)

fig.supxlabel("pre-game price (implied probability)", color=MUTED)
fig.supylabel("share of samples resolving YES", color=MUTED)
fig.suptitle("Pre-game calibration by condition, 10c buckets "
             "(≥30 samples)", color=INK, x=0.01, ha="left")
fig.tight_layout()
save(fig, "calibration-by-condition.png")


# ── 6b. By temperature ──
print("6b. By temperature")
TEMP_BANDS = [
    ("< 60°F", "temp_f < 60"),
    ("60–69°F", "temp_f >= 60 AND temp_f < 70"),
    ("70–79°F", "temp_f >= 70 AND temp_f < 80"),
    ("80°F+", "temp_f >= 80"),
]

fig, axes = plt.subplots(2, 2, figsize=(8.6, 8.6), sharex=True, sharey=True)
for ax, (label, band) in zip(axes.flat, TEMP_BANDS):
    df = calibration("pre_snap_wx",
                     f"condition_group != 'roof/dome' AND {band}")
    plot_calibration(ax, df.filter(pl.col("n_samples") >= 30))
    ax.set_title(label, color=INK, fontsize=11)
    ax.set_xticks([0, 0.5, 1])
    ax.set_yticks([0, 0.5, 1])
    ax.xaxis.set_major_formatter(CENTS)
    ax.yaxis.set_major_formatter(PCT)

fig.supxlabel("pre-game price (implied probability)", color=MUTED)
fig.supylabel("share of samples resolving YES", color=MUTED)
fig.suptitle("Pre-game calibration by temperature (outdoor), 10c buckets "
             "(≥30 samples)", color=INK, x=0.01, ha="left")
fig.tight_layout()
save(fig, "calibration-by-temperature.png")


# ── 6c. By wind ──
print("6c. By wind")
WIND_BANDS = [
    ("0–4 mph", "wind_mph < 5"),
    ("5–9 mph", "wind_mph >= 5 AND wind_mph < 10"),
    ("10+ mph", "wind_mph >= 10"),
]

fig, axes = plt.subplots(1, 3, figsize=(11, 4.2), sharex=True, sharey=True)
for ax, (label, band) in zip(axes.flat, WIND_BANDS):
    df = calibration("pre_snap_wx",
                     f"condition_group != 'roof/dome' AND {band}")
    plot_calibration(ax, df.filter(pl.col("n_samples") >= 30))
    ax.set_title(label, color=INK, fontsize=11)
    ax.set_xticks([0, 0.5, 1])
    ax.set_yticks([0, 0.5, 1])
    ax.xaxis.set_major_formatter(CENTS)
    ax.yaxis.set_major_formatter(PCT)

fig.supxlabel("pre-game price (implied probability)", color=MUTED)
fig.supylabel("share of samples resolving YES", color=MUTED)
fig.suptitle("Pre-game calibration by wind (outdoor), 10c buckets "
             "(≥30 samples)", color=INK, x=0.01, ha="left")
fig.tight_layout()
save(fig, "calibration-by-wind.png")

print("\nDone. All plots saved to write_ups/images/")
