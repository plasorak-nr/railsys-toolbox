"""Histogram plotting utilities for station-level lateness, dwell times, and run times."""

from collections.abc import Sequence

import matplotlib.pyplot as plt
import polars as pl
from matplotlib.figure import Figure

from rsys_toolbox.core import LocationSelector, remove_zzztiplocs, require_columns, selector_filter
from rsys_toolbox.plots.sectional_running_time import _maybe_duration_seconds


@remove_zzztiplocs
@selector_filter()
def plot_lateness_histogram(
    data: pl.DataFrame,
    bins: int | Sequence[float] | str = 30,
    cumulative: bool = False,
) -> Figure:
    """Plot a histogram of arrival lateness at the filtered station(s).

    Use a ``location_selector`` to restrict to a specific station. Lateness
    values are converted from seconds to minutes.

    Args:
        data: Input dataframe (full dataset or pre-filtered subset).
        bins: Number of bins (int), explicit bin edges (sequence of floats),
            or a binning strategy name (str), this argument is passed directly to ``ax.hist``.
        cumulative: When True, plot the cumulative distribution instead of counts.

    Returns:
        A matplotlib Figure containing the lateness histogram.

    Raises:
        ValueError: If required columns are missing or no valid data remains.

    """
    require_columns(data, {"Arrival lateness", "Station name", "Station abbreviation"})

    unique_stations = data.get_column("Station abbreviation").drop_nulls().unique()
    if len(unique_stations) != 1:
        raise ValueError(
            f"Expected exactly one station in input data, found: {unique_stations.to_list()}. "
            "Use a location_selector to restrict to a single station."
        )

    observations = data.drop_nulls("Arrival lateness")

    if observations.is_empty():
        raise ValueError("No valid arrival lateness observations after filtering nulls")

    lateness_minutes = (observations.get_column("Arrival lateness") / 60.0).to_list()

    station_name = observations.get_column("Station name")[0]
    tiploc = observations.get_column("Station abbreviation")[0]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(lateness_minutes, bins=bins, cumulative=cumulative, edgecolor="white", linewidth=0.4)
    ax.axvline(x=0.0, color="grey", linestyle="--", linewidth=1.0, label="On time (0)")

    ax.set_title(f"Arrival Lateness {'Cumulative ' if cumulative else ''}Distribution at {station_name} ({tiploc})")
    ax.set_xlabel("Arrival lateness (minutes)")
    ax.set_ylabel("Cumulative count" if cumulative else "Count")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()

    return fig


@remove_zzztiplocs
@selector_filter(location_selector_required=True)
def plot_dwell_histogram(
    data: pl.DataFrame,
    min_dwell_seconds: float = 10.0,
    bins: int | Sequence[float] | str = 30,
    cumulative: bool = False,
) -> Figure:
    """Plot a histogram of actual dwell times at a single station.

    A ``location_selector`` is required to pin the data to one station.
    Dwell time is computed as actual departure minus actual arrival and is
    shown in seconds.

    Args:
        data: Input dataframe (full dataset or pre-filtered subset).
        min_dwell_seconds: Dwell observations below this threshold are excluded
            (filters pass-through events).
        bins: Number of bins (int), explicit bin edges (sequence of floats),
            or a binning strategy name (str), this argument is passed directly to ``ax.hist``.
        cumulative: When True, plot the cumulative distribution instead of counts.

    Returns:
        A matplotlib Figure containing the dwell-time histogram.

    Raises:
        ValueError: If ``location_selector`` is not provided, required columns are
            missing, multiple stations remain after filtering, or no valid data remains.

    """
    require_columns(
        data,
        {
            "Station name",
            "Station abbreviation",
            "Actual arrival",
            "Actual departure",
        },
    )

    unique_stations = data.get_column("Station abbreviation").drop_nulls().unique()
    if len(unique_stations) != 1:
        raise ValueError(
            f"Expected exactly one station in input data, found: {unique_stations.to_list()}. "
            "Use a location_selector to restrict to a single station."
        )

    rows = data.drop_nulls(["Actual arrival", "Actual departure"])

    dwell_seconds = [
        d
        for row in rows.iter_rows(named=True)
        if (d := _maybe_duration_seconds(row["Actual arrival"], row["Actual departure"])) is not None
        and d >= min_dwell_seconds
    ]

    if not dwell_seconds:
        raise ValueError("No valid dwell observations after filtering")

    station_name = rows.get_column("Station name")[0]
    tiploc = rows.get_column("Station abbreviation")[0]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(dwell_seconds, bins=bins, cumulative=cumulative, edgecolor="white", linewidth=0.4)

    ax.set_title(f"Dwell Time {'Cumulative ' if cumulative else ''}Distribution — {station_name} ({tiploc})")
    ax.set_xlabel("Dwell time (seconds)")
    ax.set_ylabel("Cumulative count" if cumulative else "Count")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()

    return fig


@remove_zzztiplocs
@selector_filter()
def plot_srt_histogram(
    data: pl.DataFrame,
    location_from: LocationSelector,
    location_to: LocationSelector,
    bins: int | Sequence[float] | str = 30,
    cumulative: bool = False,
) -> Figure:
    """Plot a histogram of actual sectional running times between two stations.

    Run time is computed as actual departure from ``location_from`` to actual
    arrival at ``location_to``, matched by ``Simulation no.`` and
    ``Train name``. Median scheduled run time is shown as a vertical reference
    line.

    The ``@selector_filter`` decorator is still applied, so you can further
    restrict the data with a ``train_selector`` or ``time_selector``.

    Args:
        data: Input dataframe (full dataset or pre-filtered subset).
        location_from: Selector identifying the departure station.
        location_to: Selector identifying the arrival station.
        bins: Number of bins (int), explicit bin edges (sequence of floats),
            or a binning strategy name (str), this argument is passed directly to ``ax.hist``.
        cumulative: When True, plot the cumulative distribution instead of counts.

    Returns:
        A matplotlib Figure containing the run-time histogram.

    Raises:
        ValueError: If required columns are missing, no rows match either selector,
            no valid simulation/train pairs can be formed, or no non-null run
            time observations remain.

    """
    require_columns(
        data,
        {
            "Simulation no.",
            "Train name",
            "Station abbreviation",
            "Station name",
            "Scheduled arrival",
            "Actual arrival",
            "SchedDep",
            "Actual departure",
        },
    )

    from_rows = data.filter(location_from.get_filter()).select(
        ["Simulation no.", "Train name", "SchedDep", "Actual departure",
         "Station abbreviation", "Station name"]
    )
    to_rows = data.filter(location_to.get_filter()).select(
        ["Simulation no.", "Train name", "Scheduled arrival", "Actual arrival",
         "Station abbreviation", "Station name"]
    )

    if from_rows.is_empty():
        raise ValueError("No rows match location_from selector")
    if to_rows.is_empty():
        raise ValueError("No rows match location_to selector")

    from_label = f"{from_rows['Station name'][0]} ({from_rows['Station abbreviation'][0]})"
    to_label = f"{to_rows['Station name'][0]} ({to_rows['Station abbreviation'][0]})"
    segment_label = f"{from_label} \u2192 {to_label}"

    joined = (
        from_rows
        .rename({"SchedDep": "sched_dep", "Actual departure": "actual_dep",
                 "Station abbreviation": "_from_tiploc", "Station name": "_from_name"})
        .join(
            to_rows.rename({"Scheduled arrival": "sched_arr", "Actual arrival": "actual_arr",
                             "Station abbreviation": "_to_tiploc", "Station name": "_to_name"}),
            on=["Simulation no.", "Train name"],
        )
    )

    if joined.is_empty():
        raise ValueError(
            "No matching Simulation no./Train name pairs between location_from and location_to"
        )

    actual_seconds: list[float] = []
    scheduled_seconds: list[float] = []
    for row in joined.iter_rows(named=True):
        actual = _maybe_duration_seconds(row["actual_dep"], row["actual_arr"])
        scheduled = _maybe_duration_seconds(row["sched_dep"], row["sched_arr"])
        if actual is not None:
            actual_seconds.append(actual)
        if scheduled is not None:
            scheduled_seconds.append(scheduled)

    if not actual_seconds:
        raise ValueError("No valid run time observations after filtering nulls")

    median_scheduled = sum(scheduled_seconds) / len(scheduled_seconds) if scheduled_seconds else None

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(actual_seconds, bins=bins, cumulative=cumulative, edgecolor="white", linewidth=0.4)
    if median_scheduled is not None:
        ax.axvline(
            x=median_scheduled,
            color="grey",
            linestyle="--",
            linewidth=1.0,
            label=f"Scheduled ({median_scheduled:.0f} s)",
        )
        ax.legend()

    ax.set_title(f"Run Time {'Cumulative ' if cumulative else ''}Distribution \u2014 {segment_label}")
    ax.set_xlabel("Run time (seconds)")
    ax.set_ylabel("Cumulative count" if cumulative else "Count")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()

    return fig
