"""Example: identify and plot the worst station by punctuality."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from datetime import timedelta

from rsys_toolbox.analysis import punctuality
from rsys_toolbox.core import LocationSelector, TrainSelector
from rsys_toolbox.io.eval_manager import load
from rsys_toolbox.plots import plot_median_lateness_profile
from rsys_toolbox.analysis import search_events
from rsys_toolbox.analysis import correlation, correlation_search, punctuality, search_events

DATA_PATH = Path("assets/20260512-MIAOpt-SimData_FullMIA.csv")

data = load(DATA_PATH)

TOLERANCE = timedelta(minutes=5)

# Compute punctuality for every station
station_punctuality = punctuality(data, tolerance=TOLERANCE).sort("punctuality", descending=False)

print("Punctuality by station (worst first):")
print(station_punctuality)

# Identify the single worst station
worst_row = station_punctuality.row(0, named=True)
worst_station_name = worst_row["Station name"]
worst_punctuality = worst_row["punctuality"]


TRAIN_NAME = "1N50FB"

# print(
#     search_events(
#         data,
#         # location_selector=LocationSelector(
#         #     tiploc=worst_station_name,
#         # ),
#         train_selector=TrainSelector(headcode=TRAIN_NAME),
#     ).select('Station abbreviation')
# )
# exit()


print(f"\nWorst station: {worst_station_name} — {worst_punctuality * 100:.1f}% punctual")

# Pull only arrivals at the worst station to build the lateness distribution
worst_station_data = data.filter(
    LocationSelector(tiploc=worst_station_name).get_filter()
)

# Fall back to matching by station name if the TIPLOC filter returns nothing
if worst_station_data.is_empty():
    worst_station_data = data.filter(
        data["Station name"] == worst_station_name
    )

# Collect arrival lateness values (seconds) across all simulations
lateness_seconds = (
    worst_station_data
    .select("Arrival lateness")
    .drop_nulls()
    .get_column("Arrival lateness")
    .to_list()
)

TOP_N = 20

# Restrict the ranking panel to the 20 worst stations
worst_n = station_punctuality.head(TOP_N)
labels = worst_n.get_column("Station name").to_list()
values = [v * 100 for v in worst_n.get_column("punctuality").to_list()]
colors = ["tab:red" if name == worst_station_name else "steelblue" for name in labels]

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Left panel: top-20 worst stations
ax_rank = axes[0]
y_pos = range(len(labels))
ax_rank.barh(list(y_pos), values, color=colors, alpha=0.85)
ax_rank.set_yticks(list(y_pos))
ax_rank.set_yticklabels(labels, fontsize=9)
ax_rank.set_xlabel("Punctuality (%)")
ax_rank.set_title(f"20 worst stations by punctuality\n(red = worst)")
ax_rank.axvline(x=100, color="grey", linestyle="--", linewidth=0.8)
ax_rank.grid(axis="x", alpha=0.3)
ax_rank.invert_yaxis()  # worst at the top

CLIP_MINUTES = 30

# Right panel: arrival lateness histogram for the worst station, with overflow bin
ax_hist = axes[1]
bin_width = 300  # 5-minute bins (seconds)
clip_seconds = CLIP_MINUTES * 60

# Clamp anything beyond the clip into the last bin, and below 0 into 0
clipped = np.clip(lateness_seconds, 0, clip_seconds)
bins = list(range(0, clip_seconds + bin_width, bin_width))
ax_hist.hist(clipped, bins=bins, color="tab:red", alpha=0.8, edgecolor="white")
ax_hist.set_xlim(0, clip_seconds + bin_width)

# Replace the last x-tick label with ">30 min"
tick_positions = list(range(0, clip_seconds + bin_width + 1, bin_width))
tick_labels = [str(t // 60) for t in tick_positions]
tick_labels[-1] = f">{CLIP_MINUTES}"
ax_hist.set_xticks(tick_positions)
ax_hist.set_xticklabels(tick_labels)
ax_hist.set_xlabel("Arrival lateness (minutes)")

ax_hist.axvline(x=TOLERANCE.total_seconds(), color="grey", linestyle="--", linewidth=1.2, label=f"{int(TOLERANCE.total_seconds() // 60)}-min tolerance")
ax_hist.set_ylabel("Count")
ax_hist.set_title(
    f"Arrival lateness distribution\n{worst_station_name} — {worst_punctuality * 100:.1f}% punctual"
)
ax_hist.legend()
ax_hist.grid(axis="y", alpha=0.3)

fig.tight_layout()

output_path = "punctuality_worst_station.png"
fig.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nSaved plot to {output_path}")

# --- Second figure: per-train punctuality at the worst station ---
train_punctuality = punctuality(
    worst_station_data,
    tolerance=TOLERANCE,
    group_by=["Train name"],
).sort("punctuality", descending=False)

print(f"\nPunctuality by train at {worst_station_name}:")
print(train_punctuality)

t_labels = train_punctuality.get_column("Train name").to_list()
t_values = [v * 100 for v in train_punctuality.get_column("punctuality").to_list()]

fig2, ax2 = plt.subplots(figsize=(10, max(4, len(t_labels) * 0.35)))
t_pos = range(len(t_labels))
ax2.barh(list(t_pos), t_values, color="steelblue", alpha=0.85)
ax2.set_yticks(list(t_pos))
ax2.set_yticklabels(t_labels, fontsize=8)
ax2.set_xlabel("Punctuality (%)")
ax2.set_title(f"Per-train punctuality at {worst_station_name}\n(tolerance: {int(TOLERANCE.total_seconds() // 60)} min)")
ax2.axvline(x=100, color="grey", linestyle="--", linewidth=0.8)
ax2.grid(axis="x", alpha=0.3)
ax2.invert_yaxis()  # worst at the top
fig2.tight_layout()

output_path2 = "punctuality_worst_station_trains.png"
fig2.savefig(output_path2, dpi=150, bbox_inches="tight")
print(f"\nSaved train plot to {output_path2}")

# --- Third figure: arrival lateness profile for train 1N50FB ---
TRAIN_NAME = "1N50FB"
fig3 = plot_median_lateness_profile(data, train_selector=TrainSelector(headcode=TRAIN_NAME))

output_path3 = f"punctuality_arrival_lateness_{TRAIN_NAME}.png"
fig3.savefig(output_path3, dpi=150, bbox_inches="tight")
print(f"\nSaved arrival lateness profile to {output_path3}")

print(
    search_events(
        data,
        location_selector=LocationSelector(
            tiploc=worst_station_name,
        ),
        train_selector=TrainSelector(headcode=TRAIN_NAME),
    )
)
csearch = correlation_search(
    data,
    location_effect_hypothesis=LocationSelector(
        tiploc="WNBDSJ",
    ),
    train_effect_hypothesis=TrainSelector(headcode=TRAIN_NAME),
    location_cause_hypothesis=LocationSelector(tiploc="WNBDSJ"),
    max_cause_window=timedelta(minutes=5),
)

corr_bars = (
    csearch
    .filter(pl.col("correlation").is_not_null())
    .filter(pl.col("pair_count") > 10)
    .sort("correlation", descending=True)
    .with_columns(
        pl.format(
            "{} | {} | {}",
            pl.col("Station abbreviation"),
            pl.col("Scheduled track"),
            pl.col("Train name"),
        ).alias("cause_label"),
    )
)

labels = corr_bars.get_column("cause_label").to_list()
values = corr_bars.get_column("correlation").to_list()
x = range(len(labels))

plt.figure(figsize=(12, 6))
plt.bar(x, values, color="steelblue", alpha=0.85)
plt.xlabel("Candidate cause event")
plt.ylabel("Correlation")
plt.title(f"Delay candidate cause of headcode: {TRAIN_NAME} at BOL637")
plt.xticks(x, labels, rotation=75, ha="right")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

bar_output_path = "causality_search_correlation_bars.png"
plt.savefig(bar_output_path, dpi=150)
print(f"Saved bar chart to {bar_output_path}")



result = correlation(
    data,
    location_cause_hypothesis=LocationSelector(tiploc="WNBDSJ"),
    location_effect_hypothesis=LocationSelector(tiploc="WNBDSJ"),
    train_cause_hypothesis=TrainSelector(headcode="2N50FB"),
    train_effect_hypothesis=TrainSelector(headcode=TRAIN_NAME),
    max_cause_window=timedelta(minutes=5),
)



plot_df = result.with_columns(
    (pl.col("Actual departure_cause") - pl.col("SchedDep_cause")).dt.total_seconds().alias("lateness_cause"),
    (pl.col("Actual departure_effect") - pl.col("SchedDep_effect")).dt.total_seconds().alias("lateness_effect"),
).filter((pl.col("lateness_cause") > 0) & (pl.col("lateness_effect") > 0))

print(
    plot_df.select(
        "Simulation no._effect",
        "Scheduled track_cause",
        "Scheduled track_effect",
        "Actual departure_cause",
        "Actual departure_effect",
        "lateness_cause",
        "lateness_effect",
    ).head(20),
)

plt.figure(figsize=(10, 5))

plt.scatter(plot_df.get_column("lateness_cause").to_list(), plot_df.get_column("lateness_effect").to_list(), alpha=0.7)
plt.xlabel(f"Lateness cause 2N50FB at WNBDSJ [seconds]")
plt.ylabel(f"Lateness effect {TRAIN_NAME} at WNBDSJ [seconds]")
plt.title(f"{TRAIN_NAME} to 2N50FB departure delay correlation at WNBDSJ")
plt.grid(True, alpha=0.3)
plt.tight_layout()
output_path = "causality_departure_gap_scatter.png"
plt.savefig(output_path, dpi=150)
print(f"Saved plot to {output_path}")