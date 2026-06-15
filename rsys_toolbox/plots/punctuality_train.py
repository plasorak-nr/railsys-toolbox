"""Punctuality plotting utilities for train sectional profiles."""

import matplotlib.pyplot as plt
import polars as pl
from matplotlib.figure import Figure

from rsys_toolbox.core import CombinedSelector, LocationSelector, TimeSelector, TrainSelector, remove_zzztiplocs
from rsys_toolbox.plots.sectional_running_time import _build_runtime_observations, _filter_with_selectors

@remove_zzztiplocs
def plot_median_lateness_profile(
    data: pl.DataFrame,
    min_dwell_seconds: float = 10.0,
    train_selector: TrainSelector | None = None,
    location_selector: LocationSelector | None = None,
    time_selector: TimeSelector | None = None,
    combined_selector: CombinedSelector | None = None,
) -> Figure:
    """Plot median lateness by segment with an interquartile envelope.

    Lateness is computed as actual runtime minus scheduled runtime for each
    segment (dwell and run). Values can be negative when running early.

    Args:
        data: Input dataframe (full dataset or pre-filtered subset).
        min_dwell_seconds: Dwell observations below this threshold are excluded.
        train_selector: Optional train-level selector.
        location_selector: Optional location-level selector.
        time_selector: Optional time-level selector.
        combined_selector: Optional combined selector; additional selectors are
            merged into this selector when provided.

    Returns:
        A matplotlib Figure containing median lateness and IQR envelope.

    Raises:
        ValueError: If required columns are missing or the dataframe is empty.

    """
    required_columns = {
        "Station index",
        "Station name",
        "Scheduled arrival",
        "Actual arrival",
        "SchedDep",
        "Actual departure",
    }
    missing = sorted(required_columns.difference(data.columns))
    if missing:
        raise ValueError(f"data is missing required columns: {missing}")

    if data.is_empty():
        raise ValueError("data is empty")

    train_log = _filter_with_selectors(data, train_selector, location_selector, time_selector, combined_selector)
    if train_log.is_empty():
        raise ValueError("No rows matched the provided selectors")

    runtime_obs = _build_runtime_observations(train_log, min_dwell_seconds=min_dwell_seconds)
    if runtime_obs.is_empty():
        raise ValueError("No valid runtime observations after filtering missing times")

    summary = (
        runtime_obs
        .group_by("segment_order", "segment", "kind", maintain_order=True)
        .agg(
            (pl.col("actual_seconds") - pl.col("scheduled_seconds")).median().alias("lateness_median_seconds"),
            (pl.col("actual_seconds") - pl.col("scheduled_seconds")).quantile(0.25).alias("lateness_q1_seconds"),
            (pl.col("actual_seconds") - pl.col("scheduled_seconds")).quantile(0.75).alias("lateness_q3_seconds"),
        )
        .sort("segment_order")
        .with_columns(
            (pl.col("lateness_median_seconds") / 60.0).alias("lateness_median_minutes"),
            (pl.col("lateness_q1_seconds") / 60.0).alias("lateness_q1_minutes"),
            (pl.col("lateness_q3_seconds") / 60.0).alias("lateness_q3_minutes"),
        )
    )

    segments = summary.get_column("segment").to_list()
    lateness_values = summary.get_column("lateness_median_minutes").to_list()
    lateness_q1_values = summary.get_column("lateness_q1_minutes").to_list()
    lateness_q3_values = summary.get_column("lateness_q3_minutes").to_list()

    train_name = train_log.get_column("Train name")[0] if "Train name" in train_log.columns else None
    operator_code = train_log.get_column("Operator Code")[0] if "Operator Code" in train_log.columns else None

    sim_count = train_log.get_column("Simulation no.").n_unique() if "Simulation no." in train_log.columns else 1

    fig_width = max(10.0, len(segments) * 0.75)
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    x_values = list(range(len(segments)))

    ax.fill_between(x_values, lateness_q1_values, lateness_q3_values, color="tab:blue", alpha=0.2, label="IQR (Q1-Q3)")
    ax.plot(x_values, lateness_values, marker="o", label="Median lateness")
    ax.axhline(y=0.0, color="grey", linestyle="--", linewidth=1.0, label="Scheduled (0)")

    title_base = "Lateness Profile"
    if train_name and operator_code:
        title_base = f"{train_name} ({operator_code}) Lateness Profile"
    elif train_name:
        title_base = f"{train_name} Lateness Profile"

    ax.set_title(f"{title_base} - {sim_count} simulations")
    ax.set_xlabel("Segment")
    ax.set_ylabel("Lateness (minutes)")
    ax.set_xticks(x_values)
    ax.set_xticklabels(segments, rotation=45, ha="right")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    fig.tight_layout()

    return fig
