"""Sectional running-time plotting utilities."""

from datetime import date, datetime, time, timedelta

import matplotlib.pyplot as plt
import polars as pl
from matplotlib.figure import Figure

from rsys_toolbox.core import CombinedSelector, LocationSelector, TimeSelector, TrainSelector, apply_selector_filter, filter_zzztiplocs, require_columns


def _duration_seconds(start: time, end: time) -> float:
    """Return elapsed seconds between two time values with midnight rollover.

    Returns:
        Elapsed duration in seconds.

    """
    base_day = date(2000, 1, 1)
    start_dt = datetime.combine(base_day, start)
    end_dt = datetime.combine(base_day, end)
    if end_dt < start_dt:
        end_dt += timedelta(days=1)
    return (end_dt - start_dt).total_seconds()


def _maybe_duration_seconds(start: time | None, end: time | None) -> float | None:
    """Return elapsed seconds or None when either endpoint is missing.

    Returns:
        Elapsed duration in seconds, or None when either time is missing.

    """
    if start is None or end is None:
        return None
    return _duration_seconds(start, end)


def _build_runtime_observations(train_log: pl.DataFrame, min_dwell_seconds: float) -> pl.DataFrame:
    """Build one runtime observation per dwell and movement segment.

    Returns:
        Dataframe containing per-segment scheduled and actual durations.

    """
    station_col = "Station abbreviation" if "Station abbreviation" in train_log.columns else "Station name"

    partitions = train_log.partition_by("Simulation no.", maintain_order=True) if "Simulation no." in train_log.columns else [train_log]

    observations: list[dict[str, str | float | int]] = []
    for partition in partitions:
        ordered = partition.sort("Station index")

        stations = ordered.get_column(station_col).to_list()
        sched_arr = ordered.get_column("Scheduled arrival").to_list()
        actual_arr = ordered.get_column("Actual arrival").to_list()
        sched_dep = ordered.get_column("SchedDep").to_list()
        actual_dep = ordered.get_column("Actual departure").to_list()

        for idx, station in enumerate(stations):
            scheduled_dwell_seconds = _maybe_duration_seconds(sched_arr[idx], sched_dep[idx])
            actual_dwell_seconds = _maybe_duration_seconds(actual_arr[idx], actual_dep[idx])

            if (
                scheduled_dwell_seconds is not None
                and actual_dwell_seconds is not None
                and max(scheduled_dwell_seconds, actual_dwell_seconds) >= min_dwell_seconds
            ):
                observations.append({
                    "segment_order": 2 * idx,
                    "segment": f"{station} dwell",
                    "kind": "Dwell",
                    "scheduled_seconds": scheduled_dwell_seconds,
                    "actual_seconds": actual_dwell_seconds,
                })

            if idx + 1 >= len(stations):
                continue

            next_station = stations[idx + 1]
            scheduled_run_seconds = _maybe_duration_seconds(sched_dep[idx], sched_arr[idx + 1])
            actual_run_seconds = _maybe_duration_seconds(actual_dep[idx], actual_arr[idx + 1])
            if scheduled_run_seconds is None or actual_run_seconds is None:
                continue

            observations.append({
                "segment_order": (2 * idx) + 1,
                "segment": f"{station} → {next_station}",
                "kind": "Run",
                "scheduled_seconds": scheduled_run_seconds,
                "actual_seconds": actual_run_seconds,
            })

    return pl.DataFrame(observations)


def plot_median_runtime_profile(
    data: pl.DataFrame,
    min_dwell_seconds: float = 10.0,
    remove_zzztiplocs: bool = True,
    combined_selector: CombinedSelector | None = None,
    location_selector: LocationSelector | None = None,
    time_selector: TimeSelector | None = None,
    train_selector: TrainSelector | None = None,
) -> Figure:
    """Plot median actual runtime versus scheduled runtime by consecutive station segment.

    The x-axis is a consecutive station pair segment sequence, including:
    - dwell segments at each station (arrival -> departure)
    - movement segments between consecutive stations (departure -> next arrival)

    If multiple simulations are present, actual values are aggregated by median,
    and a blue envelope shows the interquartile range ($Q_1$ to $Q_3$).

    Args:
        data: Input dataframe (full dataset or pre-filtered subset).
        min_dwell_seconds: Dwell observations below this threshold are excluded.
        remove_zzztiplocs: Whether to exclude rows where ``Station abbreviation``
            starts with ``ZZZ``. Defaults to True.
        combined_selector: Optional combined train/location/time selector.
        location_selector: Optional location selector.
        time_selector: Optional time selector.
        train_selector: Optional train selector.

    Returns:
        A matplotlib Figure containing scheduled and median-actual runtime lines.

    Raises:
        ValueError: If required columns are missing or the dataframe is empty.

    """
    data = apply_selector_filter(
        data,
        combined_selector=combined_selector,
        location_selector=location_selector,
        time_selector=time_selector,
        train_selector=train_selector,
    )
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
            pl.col("scheduled_seconds").median().alias("scheduled_median_seconds"),
            pl.col("actual_seconds").median().alias("actual_median_seconds"),
            pl.col("actual_seconds").quantile(0.25).alias("actual_q1_seconds"),
            pl.col("actual_seconds").quantile(0.75).alias("actual_q3_seconds"),
        )
        .sort("segment_order")
        .with_columns(
            (pl.col("scheduled_median_seconds") / 60.0).alias("scheduled_median_minutes"),
            (pl.col("actual_median_seconds") / 60.0).alias("actual_median_minutes"),
            (pl.col("actual_q1_seconds") / 60.0).alias("actual_q1_minutes"),
            (pl.col("actual_q3_seconds") / 60.0).alias("actual_q3_minutes"),
        )
    )

    segments = summary.get_column("segment").to_list()
    scheduled_values = summary.get_column("scheduled_median_minutes").to_list()
    actual_values = summary.get_column("actual_median_minutes").to_list()
    actual_q1_values = summary.get_column("actual_q1_minutes").to_list()
    actual_q3_values = summary.get_column("actual_q3_minutes").to_list()

    train_name = data.get_column("Train name")[0] if "Train name" in data.columns else None
    operator_code = data.get_column("Operator Code")[0] if "Operator Code" in data.columns else None

    sim_count = data.get_column("Simulation no.").n_unique() if "Simulation no." in data.columns else 1

    fig_width = max(10.0, len(segments) * 0.75)
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    x_values = list(range(len(segments)))

    ax.fill_between(x_values, actual_q1_values, actual_q3_values, color="tab:blue", alpha=0.2, label="IQR (Q1-Q3)")
    ax.plot(x_values, actual_values, marker="o", label="Median")
    ax.plot(x_values, scheduled_values, marker="o", label="Scheduled")

    title_base = "Runtime Profile"
    if train_name and operator_code:
        title_base = f"{train_name} ({operator_code}) Runtime Profile"
    elif train_name:
        title_base = f"{train_name} Runtime Profile"

    ax.set_title(f"{title_base} - {sim_count} simulations")
    ax.set_xlabel("Segment")
    ax.set_ylabel("Runtime (minutes)")
    ax.set_xticks(x_values)
    ax.set_xticklabels(segments, rotation=45, ha="right")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    fig.tight_layout()

    return fig
