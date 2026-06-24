"""An example of using the causality functionality of rsys_toolbox."""

from datetime import timedelta

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from rsys_toolbox.analysis import correlation, correlation_search, punctuality, search_events
from rsys_toolbox.core import LocationSelector, TrainSelector
from rsys_toolbox.io.eval_manager import load

data = load("assets/MRH S1 Eval Manager 2105.csv")
print(
    punctuality(
        data,
    ).sort(by="punctuality", descending=False)
)

TIPLOC = "BGRN"

print(
    punctuality(
        data,
        location_selector=LocationSelector(
            tiploc=TIPLOC,
        ),
        group_by=[
            "Station name",
            "Scheduled track",
        ],
    ).sort(by="punctuality", descending=False)
)

TRACK = "BGRN U-1"

print(
    punctuality(data, location_selector=LocationSelector(tiploc=TIPLOC, track=TRACK), group_by=["Station name", "Scheduled track", "Train name"]).sort(
        by="punctuality", descending=False
    )
)


print(
    search_events(
        data,
        location_selector=LocationSelector(
            track=TRACK,
            tiploc=TIPLOC,
        ),
    )
    .select("Train name")
    .unique()
)

HEADCODE = "2U52GG"

csearch = correlation_search(
    data,
    location_effect_hypothesis=LocationSelector(
        track=TRACK,
        tiploc=TIPLOC,
    ),
    train_effect_hypothesis=TrainSelector(headcode=HEADCODE),
    location_cause_hypothesis=LocationSelector(tiploc=TIPLOC),
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
plt.title(f"Delay candidate cause of headcode: {TIPLOC} at track: {TRACK}")
plt.xticks(x, labels, rotation=75, ha="right")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

bar_output_path = "causality_search_correlation_bars.png"
plt.savefig(bar_output_path, dpi=150)
print(f"Saved bar chart to {bar_output_path}")


OFFENDING_HEADCODE = "1S47ET"

result = correlation(
    data,
    location_cause_hypothesis=LocationSelector(tiploc=TIPLOC),
    location_effect_hypothesis=LocationSelector(track=TRACK),
    train_cause_hypothesis=TrainSelector(headcode=OFFENDING_HEADCODE),
    train_effect_hypothesis=TrainSelector(headcode=HEADCODE),
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
plt.xlabel(f"Lateness cause {OFFENDING_HEADCODE} at {TIPLOC} [seconds]")
plt.ylabel(f"Lateness effect {HEADCODE} at {TIPLOC} [seconds]")
plt.title(f"{HEADCODE} to {OFFENDING_HEADCODE} departure delay correlation at {TIPLOC}")
plt.grid(True, alpha=0.3)
plt.tight_layout()
output_path = "causality_departure_gap_scatter.png"
plt.savefig(output_path, dpi=150)
print(f"Saved plot to {output_path}")

print(f"Correlation {np.corrcoef(plot_df.get_column('lateness_cause').to_numpy(), plot_df.get_column('lateness_effect').to_numpy())[0, 1] * 100.0:0f}%")
