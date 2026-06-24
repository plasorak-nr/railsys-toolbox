"""Flighting analysis helpers for train ordering across simulations."""

from typing import Literal

import polars as pl

from rsys_toolbox.core import remove_zzztiplocs, require_columns

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


def _station_flighting_events(data: pl.DataFrame, event: FlightingEvent, include_track: bool) -> list[dict[str, object]]:
    """Build station event rows for ordering comparisons.

    Returns:
        Event dictionaries grouped later by station and simulation.

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

    events = []
    for event_index, row in enumerate(data.to_dicts()):
        scheduled_time = row[scheduled_time_col]
        actual_time = row[actual_time_col]
        if scheduled_time is None or actual_time is None:
            continue

        resource_label = f"{row['Station abbreviation']} ({row['Station name']})"
        if include_track:
            resource_label = f"{resource_label} / {row['Scheduled track']}"

        events.append({
            "simulation": row["Simulation no."],
            "resource_label": resource_label,
            "event_id": f"{row['Train no.']}|{row['Train name']}|{row['Station index']}|{event_index}",
            "train_name": row["Train name"],
            "train_no": row["Train no."],
            "scheduled_time": scheduled_time,
            "actual_time": actual_time,
        })

    return events


def _section_flighting_events(data: pl.DataFrame, event: FlightingEvent) -> list[dict[str, object]]:
    """Build section-entry event rows for ordering comparisons.

    Returns:
        Event dictionaries grouped later by section and simulation.

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

    events = []
    ordered_data = data.sort("Simulation no.", "Train no.", "Station index")
    for partition in ordered_data.partition_by("Simulation no.", "Train no.", maintain_order=True):
        rows = partition.to_dicts()
        for section_index, row in enumerate(rows[:-1]):
            next_row = rows[section_index + 1]
            time_row = next_row if event == "arrival" else row
            scheduled_time = time_row[scheduled_time_col]
            actual_time = time_row[actual_time_col]
            if scheduled_time is None or actual_time is None:
                continue

            events.append({
                "simulation": row["Simulation no."],
                "resource_label": f"{row['Station abbreviation']} -> {next_row['Station abbreviation']}",
                "event_id": f"{row['Train no.']}|{row['Train name']}|{row['Station index']}",
                "train_name": row["Train name"],
                "train_no": row["Train no."],
                "scheduled_time": scheduled_time,
                "actual_time": actual_time,
            })

    return events


def _has_out_of_order_trains(events: list[dict[str, object]]) -> bool:
    """Return whether scheduled and actual event orders differ.

    Returns:
        Whether actual event order differs from scheduled event order.

    """
    scheduled_order = [
        event["event_id"] for event in sorted(events, key=lambda event: (event["scheduled_time"], event["train_name"], event["train_no"], event["event_id"]))
    ]
    actual_order = [
        event["event_id"] for event in sorted(events, key=lambda event: (event["actual_time"], event["train_name"], event["train_no"], event["event_id"]))
    ]

    return scheduled_order != actual_order


def _out_of_order_flighting_summary(events: list[dict[str, object]], max_items: int | None) -> pl.DataFrame:
    """Summarise the proportion of comparable simulations with reordered trains.

    Returns:
        Resource-level summary sorted by highest out-of-order proportion.

    """
    grouped_events: dict[tuple[object, object], list[dict[str, object]]] = {}
    for event in events:
        grouped_events.setdefault((event["resource_label"], event["simulation"]), []).append(event)

    summary_by_resource: dict[object, tuple[int, int]] = {}
    for (resource_label, _simulation), group_events in grouped_events.items():
        unique_event_count = len({event["event_id"] for event in group_events})
        if unique_event_count < 2:
            continue

        simulation_count, out_of_order_simulation_count = summary_by_resource.get(resource_label, (0, 0))
        simulation_count += 1
        if _has_out_of_order_trains(group_events):
            out_of_order_simulation_count += 1
        summary_by_resource[resource_label] = (simulation_count, out_of_order_simulation_count)

    rows = [
        {
            "resource_label": resource_label,
            "simulation_count": simulation_count,
            "out_of_order_simulation_count": out_of_order_simulation_count,
        }
        for resource_label, (simulation_count, out_of_order_simulation_count) in summary_by_resource.items()
    ]
    if not rows:
        return pl.DataFrame(
            schema={
                "resource_label": pl.String,
                "simulation_count": pl.Int64,
                "out_of_order_simulation_count": pl.Int64,
                "out_of_order_simulation_proportion": pl.Float64,
            }
        )

    summary = (
        pl
        .DataFrame(rows)
        .with_columns((pl.col("out_of_order_simulation_count") / pl.col("simulation_count")).alias("out_of_order_simulation_proportion"))
        .sort(["out_of_order_simulation_proportion", "out_of_order_simulation_count", "resource_label"], descending=[True, True, False])
    )

    if max_items is not None:
        return summary.head(max_items)

    return summary


@remove_zzztiplocs
def build_out_of_order_flighting_summary(
    data: pl.DataFrame,
    mode: FlightingMode = "station",
    event: FlightingEvent = "departure",
    include_track: bool = False,
    max_items: int | None = None,
) -> pl.DataFrame:
    """Build out-of-order flighting rates by station or section.

    Args:
        data: Filtered or unfiltered Eval Manager dataframe.
        mode: Whether to compare order at each station or over each section.
        event: Timestamp pair used for scheduled-versus-actual ordering.
        include_track: Whether station labels should include scheduled track.
        max_items: Optional number of highest-rate resources to keep.

    Returns:
        A dataframe sorted by descending out-of-order simulation proportion.

    Raises:
        ValueError: If required columns are missing, mode is invalid, or no
            comparable station/section has at least two trains in a simulation.

    """
    if data.is_empty():
        raise ValueError("data is empty")
    if max_items is not None and max_items < 1:
        raise ValueError("max_items must be at least 1 when provided")

    if mode == "station":
        events = _station_flighting_events(data, event=event, include_track=include_track)
    elif mode == "section":
        events = _section_flighting_events(data, event=event)
    else:
        raise ValueError("mode must be one of: section, station")

    summary = _out_of_order_flighting_summary(events, max_items=max_items)
    if summary.is_empty():
        raise ValueError("No comparable station or section had at least two trains in a simulation")

    return summary
