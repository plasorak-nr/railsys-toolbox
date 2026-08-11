"""Flighting analysis helpers for train ordering across simulations."""

from typing import Literal

import polars as pl

from rsys_toolbox.core import filter_zzztiplocs, require_columns

FlightingMode = Literal["station", "section"]
FlightingEvent = Literal["arrival", "departure"]

_EVENT_TIME_COLUMNS: dict[FlightingEvent, tuple[str, str]] = {
    "arrival": ("Scheduled arrival", "Actual arrival"),
    "departure": ("SchedDep", "Actual departure"),
}


def _event_columns(event: FlightingEvent) -> tuple[str, str]:
    """Return the scheduled and actual timestamp columns for a flighting event.

    Returns:
        Scheduled and actual timestamp column names.

    Raises:
        ValueError: If ``event`` is not supported.

    """
    if event not in _EVENT_TIME_COLUMNS:
        expected = ", ".join(sorted(_EVENT_TIME_COLUMNS))
        raise ValueError(f"event must be one of: {expected}")

    return _EVENT_TIME_COLUMNS[event]


def _station_flighting_events(data: pl.DataFrame, event: FlightingEvent, include_track: bool) -> pl.DataFrame:
    """Build station event rows for ordering comparisons.

    Returns:
        Event dataframe grouped later by station and simulation.

    """
    scheduled_time_col, actual_time_col = _event_columns(event)
    required_columns = {
        "Simulation no.",
        "Station index",
        "Station abbreviation",
        "Station name",
        "Train no.",
        "Train name",
        scheduled_time_col,
        actual_time_col,
    }
    if include_track:
        required_columns.add("Scheduled track")
    require_columns(data, required_columns)

    base = (
        data
        .with_row_index("_event_index")
        .filter(pl.col(scheduled_time_col).is_not_null() & pl.col(actual_time_col).is_not_null())
        .with_columns(
            pl.format("{} ({})", pl.col("Station abbreviation"), pl.col("Station name")).alias("_resource_label"),
        )
    )
    if include_track:
        base = base.with_columns(
            pl.format("{} / {}", pl.col("_resource_label"), pl.col("Scheduled track")).alias("_resource_label"),
        )
    return base.select(
        pl.col("Simulation no.").alias("simulation"),
        pl.col("_resource_label").alias("resource_label"),
        pl.format(
            "{}|{}|{}|{}",
            pl.col("Train no.").cast(pl.String),
            pl.col("Train name"),
            pl.col("Station index").cast(pl.String),
            pl.col("_event_index").cast(pl.String),
        ).alias("event_id"),
        pl.col("Train name").alias("train_name"),
        pl.col("Train no.").alias("train_no"),
        pl.col(scheduled_time_col).alias("scheduled_time"),
        pl.col(actual_time_col).alias("actual_time"),
    )


def _section_flighting_events(data: pl.DataFrame, event: FlightingEvent) -> pl.DataFrame:
    """Build section-entry event rows for ordering comparisons.

    Returns:
        Event dataframe grouped later by section and simulation.

    """
    scheduled_time_col, actual_time_col = _event_columns(event)
    require_columns(
        data,
        {
            "Simulation no.",
            "Station index",
            "Station abbreviation",
            "Train no.",
            "Train name",
            scheduled_time_col,
            actual_time_col,
        },
    )

    partition_cols = ["Simulation no.", "Train no."]
    base = (
        data
        .sort("Simulation no.", "Train no.", "Station index")
        .with_columns(
            pl.col("Station abbreviation").shift(-1).over(partition_cols).alias("_next_station_abbr"),
            pl.col(scheduled_time_col).shift(-1).over(partition_cols).alias("_next_scheduled_time"),
            pl.col(actual_time_col).shift(-1).over(partition_cols).alias("_next_actual_time"),
        )
        .filter(pl.col("_next_station_abbr").is_not_null())
    )

    if event == "arrival":
        scheduled_time_expr = pl.col("_next_scheduled_time")
        actual_time_expr = pl.col("_next_actual_time")
    else:
        scheduled_time_expr = pl.col(scheduled_time_col)
        actual_time_expr = pl.col(actual_time_col)

    return (
        base
        .filter(scheduled_time_expr.is_not_null() & actual_time_expr.is_not_null())
        .select(
            pl.col("Simulation no.").alias("simulation"),
            pl.format("{} → {}", pl.col("Station abbreviation"), pl.col("_next_station_abbr")).alias("resource_label"),
            pl.format(
                "{}|{}|{}",
                pl.col("Train no.").cast(pl.String),
                pl.col("Train name"),
                pl.col("Station index").cast(pl.String),
            ).alias("event_id"),
            pl.col("Train name").alias("train_name"),
            pl.col("Train no.").alias("train_no"),
            scheduled_time_expr.alias("scheduled_time"),
            actual_time_expr.alias("actual_time"),
        )
    )


def _out_of_order_flighting_summary(events: pl.DataFrame) -> pl.DataFrame:
    """Summarise the proportion of comparable simulations with reordered trains.

    Returns:
        Resource-level summary sorted by highest out-of-order proportion.

    """
    group_cols = ["resource_label", "simulation"]
    tie_break = ["train_name", "train_no", "event_id"]

    # Drop (resource, simulation) groups that have fewer than 2 unique events — incomparable
    events_filtered = events.filter(pl.col("event_id").n_unique().over(group_cols) >= 2)

    if events_filtered.is_empty():
        return pl.DataFrame(
            schema={
                "resource_label": pl.String,
                "simulation_count": pl.Int64,
                "out_of_order_simulation_count": pl.Int64,
                "out_of_order_simulation_proportion": pl.Float64,
            }
        )

    # Build the ordered event_id sequence for each group under scheduled and actual times;
    # concatenate as a string so a simple != detects any reordering
    sched_seq = (
        events_filtered
        .sort(group_cols + ["scheduled_time"] + tie_break)
        .group_by(group_cols, maintain_order=True)
        .agg(pl.col("event_id").str.concat("|").alias("scheduled_seq"))
    )
    actual_seq = (
        events_filtered
        .sort(group_cols + ["actual_time"] + tie_break)
        .group_by(group_cols, maintain_order=True)
        .agg(pl.col("event_id").str.concat("|").alias("actual_seq"))
    )

    return (
        sched_seq
        .join(actual_seq, on=group_cols)
        .group_by("resource_label")
        .agg(
            pl.len().cast(pl.Int64).alias("simulation_count"),
            (pl.col("scheduled_seq") != pl.col("actual_seq")).sum().cast(pl.Int64).alias("out_of_order_simulation_count"),
        )
        .with_columns(
            (pl.col("out_of_order_simulation_count") / pl.col("simulation_count")).alias("out_of_order_simulation_proportion")
        )
        .sort(["out_of_order_simulation_proportion", "out_of_order_simulation_count", "resource_label"], descending=[True, True, False])
    )


def build_out_of_order_flighting_summary(
    data: pl.DataFrame,
    mode: FlightingMode = "station",
    event: FlightingEvent = "departure",
    include_track: bool = False,
    remove_zzztiplocs: bool = True,
) -> pl.DataFrame:
    """Build out-of-order flighting rates by station or section.

    Args:
        data: Filtered or unfiltered Eval Manager dataframe.
        mode: Whether to compare order at each station or over each section.
        event: Timestamp pair used for scheduled-versus-actual ordering.
        include_track: Whether tracks should also be considered when doing the flighting.
        remove_zzztiplocs: Whether to apply
            [filter_zzztiplocs][rsys_toolbox.core.filter_zzztiplocs]
            before the computation. If ``True`` (default), rows whose
            ``Station abbreviation`` starts with ``ZZZ`` are excluded.

    Returns:
        A dataframe sorted by descending out-of-order simulation proportion.

    Raises:
        ValueError: If required columns are missing, mode is invalid, or no
            comparable station/section has at least two trains in a simulation.

    """
    if data.is_empty():
        raise ValueError("data is empty")

    if remove_zzztiplocs:
        data = filter_zzztiplocs(data)

    if mode == "station":
        events = _station_flighting_events(data, event=event, include_track=include_track)
    elif mode == "section":
        events = _section_flighting_events(data, event=event)
    else:
        raise ValueError("mode must be one of: section, station")

    summary = _out_of_order_flighting_summary(events)
    if summary.is_empty():
        raise ValueError("No comparable station or section had at least two trains in a simulation")

    return summary
