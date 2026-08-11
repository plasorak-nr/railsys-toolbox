"""Punctuality plotting utilities for train sectional profiles."""

import matplotlib.pyplot as plt
import polars as pl
from matplotlib.figure import Figure

from rsys_toolbox.core import filter_zzztiplocs, require_columns, selector_filter
from rsys_toolbox.plots.sectional_running_time import _build_runtime_observations


@selector_filter()
def plot_median_lateness_profile(
    data: pl.DataFrame,
    remove_zzztiplocs: bool = True,
) -> Figure:
    """Plot median arrival lateness per station with an interquartile envelope.

    Lateness is computed as actual arrival minus scheduled arrival at each
    station, aggregated across all simulations. This shows the cumulative
    punctuality profile of a train along its journey.

    Args:
        data: Input dataframe (full dataset or pre-filtered subset).
        remove_zzztiplocs: Whether to exclude rows where ``Station abbreviation``
            starts with ``ZZZ``. Defaults to True.

    Returns:
        A matplotlib Figure containing median arrival lateness and IQR envelope.

    Raises:
        ValueError: If required columns are missing or the dataframe is empty.

    """
    if remove_zzztiplocs:
        data = filter_zzztiplocs(data)
    required_columns = {
        "Station index",
        "Station name",
        "Arrival lateness",
    }
    require_columns(data, required_columns)

    if data.is_empty():
        raise ValueError("data is empty")

    summary = (
        data
        .drop_nulls("Arrival lateness")
        .group_by("Station index", "Station name", "Station abbreviation")
        .agg(
            (pl.col("Arrival lateness") / 60.0).median().alias("lateness_median_minutes"),
            (pl.col("Arrival lateness") / 60.0).quantile(0.25).alias("lateness_q1_minutes"),
            (pl.col("Arrival lateness") / 60.0).quantile(0.75).alias("lateness_q3_minutes"),
        )
        .sort("Station index")
    )

    if summary.is_empty():
        raise ValueError("No valid arrival lateness observations after filtering nulls")

    stations = summary.get_column("Station name").to_list()
    tiplocs = summary.get_column("Station abbreviation").to_list()
    stations = [f"{s} ({t})" for s, t in zip(stations, tiplocs)]
    lateness_values = summary.get_column("lateness_median_minutes").to_list()
    lateness_q1_values = summary.get_column("lateness_q1_minutes").to_list()
    lateness_q3_values = summary.get_column("lateness_q3_minutes").to_list()

    train_name = data.get_column("Train name")[0] if "Train name" in data.columns else None
    operator_code = data.get_column("Operator Code")[0] if "Operator Code" in data.columns else None
    sim_count = data.get_column("Simulation no.").n_unique() if "Simulation no." in data.columns else 1

    fig_width = max(10.0, len(stations) * 0.75)
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    x_values = list(range(len(stations)))

    ax.fill_between(x_values, lateness_q1_values, lateness_q3_values, color="tab:blue", alpha=0.2, label="IQR (Q1-Q3)")
    ax.plot(x_values, lateness_values, marker="o", label="Median arrival lateness")
    ax.axhline(y=0.0, color="grey", linestyle="--", linewidth=1.0, label="On time (0)")

    title_base = "Arrival Lateness Profile"
    if train_name and operator_code:
        title_base = f"{train_name} ({operator_code}) Arrival Lateness Profile"
    elif train_name:
        title_base = f"{train_name} Arrival Lateness Profile"

    ax.set_title(f"{title_base} ({sim_count} simulations)")
    ax.set_xlabel("TIPLOC")
    ax.set_ylabel("Arrival lateness (minutes)")
    ax.set_xticks(x_values)
    ax.set_xticklabels(stations, rotation=45, ha="right")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    fig.tight_layout()

    return fig


@selector_filter()
def plot_timeloss_profile(
    data: pl.DataFrame,
    min_dwell_seconds: float = 10.0,
    remove_zzztiplocs: bool = True,
) -> Figure:
    """Plot median time loss per segment with an interquartile envelope.

    Time loss is computed as actual runtime minus scheduled runtime for each
    segment (dwell and run). Positive values mean time was lost; negative
    values mean time was recovered.

    Args:
        data: Input dataframe (full dataset or pre-filtered subset).
        min_dwell_seconds: Dwell observations below this threshold are excluded.
        remove_zzztiplocs: Whether to exclude rows where ``Station abbreviation``
            starts with ``ZZZ``. Defaults to True.

    Returns:
        A matplotlib Figure containing median time loss and IQR envelope.

    Raises:
        ValueError: If required columns are missing or the dataframe is empty.

    """
    if remove_zzztiplocs:
        data = filter_zzztiplocs(data)
    required_columns = {
        "Station index",
        "Station name",
        "Scheduled arrival",
        "Actual arrival",
        "SchedDep",
        "Actual departure",
    }
    require_columns(data, required_columns)

    if data.is_empty():
        raise ValueError("data is empty")

    runtime_obs = _build_runtime_observations(data, min_dwell_seconds=min_dwell_seconds)
    if runtime_obs.is_empty():
        raise ValueError("No valid runtime observations after filtering missing times")

    summary = (
        runtime_obs
        .group_by("segment_order", "segment", "kind", maintain_order=True)
        .agg(
            (pl.col("actual_seconds") - pl.col("scheduled_seconds")).median().alias("timeloss_median_seconds"),
            (pl.col("actual_seconds") - pl.col("scheduled_seconds")).quantile(0.25).alias("timeloss_q1_seconds"),
            (pl.col("actual_seconds") - pl.col("scheduled_seconds")).quantile(0.75).alias("timeloss_q3_seconds"),
        )
        .sort("segment_order")
        .with_columns(
            (pl.col("timeloss_median_seconds") / 60.0).alias("timeloss_median_minutes"),
            (pl.col("timeloss_q1_seconds") / 60.0).alias("timeloss_q1_minutes"),
            (pl.col("timeloss_q3_seconds") / 60.0).alias("timeloss_q3_minutes"),
        )
    )

    segments = summary.get_column("segment").to_list()
    timeloss_values = summary.get_column("timeloss_median_minutes").to_list()
    timeloss_q1_values = summary.get_column("timeloss_q1_minutes").to_list()
    timeloss_q3_values = summary.get_column("timeloss_q3_minutes").to_list()

    train_name = data.get_column("Train name")[0] if "Train name" in data.columns else None
    operator_code = data.get_column("Operator Code")[0] if "Operator Code" in data.columns else None
    sim_count = data.get_column("Simulation no.").n_unique() if "Simulation no." in data.columns else 1

    fig_width = max(10.0, len(segments) * 0.75)
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    x_values = list(range(len(segments)))

    ax.fill_between(x_values, timeloss_q1_values, timeloss_q3_values, color="tab:blue", alpha=0.2, label="IQR (Q1-Q3)")
    ax.plot(x_values, timeloss_values, marker="o", label="Median time loss")
    ax.axhline(y=0.0, color="grey", linestyle="--", linewidth=1.0, label="No time loss (0)")

    title_base = "Time Loss Profile"
    if train_name and operator_code:
        title_base = f"{train_name} ({operator_code}) Time Loss Profile"
    elif train_name:
        title_base = f"{train_name} Time Loss Profile"

    ax.set_title(f"{title_base} — {sim_count} simulations")
    ax.set_xlabel("Segment")
    ax.set_ylabel("Time loss (minutes)")
    ax.set_xticks(x_values)
    ax.set_xticklabels(segments, rotation=45, ha="right")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    fig.tight_layout()

    return fig
