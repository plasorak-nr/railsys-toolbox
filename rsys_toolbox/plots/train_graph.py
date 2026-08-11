"""Train graph plotting utilities."""

from datetime import date, datetime, time, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from matplotlib.figure import Figure

from rsys_toolbox.core import CombinedSelector, LocationSelector, TimeSelector, TrainSelector, apply_selector_filter, filter_zzztiplocs, require_columns


def _times_to_monotonic_datetimes(times: list[time]) -> list[datetime]:
    """Convert times into increasing datetimes and handle midnight rollover.

    Returns:
        A monotonic datetime list built from the input time values.

    """
    if not times:
        return []

    base_day = date(2000, 1, 1)
    monotonic: list[datetime] = []
    day_offset = 0
    previous_dt: datetime | None = None

    for t in times:
        current_dt = datetime.combine(base_day + timedelta(days=day_offset), t)
        if previous_dt is not None and current_dt < previous_dt:
            day_offset += 1
            current_dt = datetime.combine(base_day + timedelta(days=day_offset), t)

        monotonic.append(current_dt)
        previous_dt = current_dt

    return monotonic


def _positions_from_timepoints(timepoints: list[datetime], speed_kmh: float) -> list[float]:
    """Compute cumulative position in km from elapsed time and constant speed.

    Returns:
        Position values in kilometers for each input timepoint.

    """
    if not timepoints:
        return []

    start = timepoints[0]
    return [((tp - start).total_seconds() / 3600.0) * speed_kmh for tp in timepoints]


def _align_departures_to_arrivals(arrivals: list[datetime], departures: list[time]) -> list[datetime]:
    """Convert departures to monotonic datetimes aligned with arrival day offsets.

    Returns:
        Departure datetimes where each value is on/after its corresponding arrival.

    """
    aligned: list[datetime] = []

    for arr_dt, dep_t in zip(arrivals, departures, strict=True):
        dep_dt = datetime.combine(arr_dt.date(), dep_t)
        if dep_dt < arr_dt:
            dep_dt += timedelta(days=1)
        aligned.append(dep_dt)

    return aligned


def _build_weaved_path(
    arrivals: list[datetime],
    departures: list[datetime],
    positions: list[float],
) -> tuple[list[datetime], list[float]]:
    """Create a path that includes arrival->departure dwell at each station.

    Returns:
        X/Y coordinates for plotting a woven train path.

    """
    x_values: list[datetime] = []
    y_values: list[float] = []

    for arr_dt, dep_dt, pos in zip(arrivals, departures, positions, strict=True):
        x_values.extend([arr_dt, dep_dt])
        y_values.extend([pos, pos])

    return x_values, y_values


def plot_train_graph(
    data: pl.DataFrame,
    simulation: int,
    speed_kmh: float = 100.0,
    remove_zzztiplocs: bool = True,
    combined_selector: CombinedSelector | None = None,
    location_selector: LocationSelector | None = None,
    time_selector: TimeSelector | None = None,
    train_selector: TrainSelector | None = None,
    data_filter: pl.Expr | None = None,
) -> Figure:
    """Plot a train trajectory with time on x-axis and estimated position on y-axis.

    The position is inferred from elapsed time assuming a constant train speed.
    Both scheduled and actual arrival time trajectories are drawn.

    Args:
        data: Input dataframe (full dataset or already-filtered train log).
        simulation: Simulation number to isolate one run.
        speed_kmh: Constant speed used for the position estimate.
        remove_zzztiplocs: Whether to exclude rows where ``Station abbreviation``
            starts with ``ZZZ``. Defaults to True.
        combined_selector: Optional combined train/location/time selector.
        location_selector: Optional location selector.
        time_selector: Optional time selector.
        train_selector: Optional train selector.
        data_filter: Optional raw Polars expression applied before selectors.

    Returns:
        A matplotlib Figure containing the train graph.

    Raises:
        ValueError: If required columns are missing or the dataframe is empty.

    """
    if remove_zzztiplocs:
        data = filter_zzztiplocs(data)
    data = apply_selector_filter(
        data,
        combined_selector=combined_selector,
        location_selector=location_selector,
        time_selector=time_selector,
        train_selector=train_selector,
        data_filter=data_filter,
    )
    required_columns = {
        "Station name",
        "Station index",
        "Scheduled arrival",
        "Actual arrival",
        "SchedDep",
        "Actual departure",
        "Train name",
    }
    require_columns(data, required_columns)

    if data.is_empty():
        raise ValueError("data is empty")

    sim_value = int(simulation) if isinstance(simulation, str) else simulation
    train_log = data.filter(pl.col("Simulation no.") == sim_value)

    if train_log.is_empty():
        raise ValueError("No rows matched the provided simulation")

    simulation_count = train_log.get_column("Simulation no.").n_unique()
    if simulation_count != 1:
        raise ValueError("plot_train_graph requires exactly one simulation after filtering; provide simulation=")

    train_log = train_log.sort("Station index")

    train_name = train_log.get_column("Train name")[0]
    operator_code = train_log.get_column("Operator Code")[0] if "Operator Code" in train_log.columns else None

    scheduled_times = train_log.get_column("Scheduled arrival").to_list()
    actual_times = train_log.get_column("Actual arrival").to_list()
    scheduled_departures = train_log.get_column("SchedDep").to_list()
    actual_departures = train_log.get_column("Actual departure").to_list()

    scheduled_dt = _times_to_monotonic_datetimes(scheduled_times)
    actual_dt = _times_to_monotonic_datetimes(actual_times)

    # Derive one position profile from the scheduled trajectory and reuse it
    # for actual timestamps, so each station/tiploc keeps the scheduled position.
    scheduled_positions = _positions_from_timepoints(scheduled_dt, speed_kmh)
    actual_positions = scheduled_positions

    scheduled_dep_dt = _align_departures_to_arrivals(scheduled_dt, scheduled_departures)
    actual_dep_dt = _align_departures_to_arrivals(actual_dt, actual_departures)

    scheduled_x, scheduled_y = _build_weaved_path(scheduled_dt, scheduled_dep_dt, scheduled_positions)
    actual_x, actual_y = _build_weaved_path(actual_dt, actual_dep_dt, actual_positions)
    # Preserve Matplotlib date-unit handling so date-aware locators/formatters are applied.
    scheduled_x_values = np.array(scheduled_x, dtype="datetime64[us]")
    actual_x_values = np.array(actual_x, dtype="datetime64[us]")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(scheduled_x_values, scheduled_y, marker="o", label="Scheduled")
    ax.plot(actual_x_values, actual_y, marker="o", label="Actual")

    station_labels = train_log.get_column("Station name").to_list()
    for y in scheduled_positions:
        ax.axhline(y=y, color="grey", alpha=0.2, linewidth=0.8, zorder=0)

    ax.set_yticks(scheduled_positions)
    ax.set_yticklabels(station_labels)

    if operator_code:
        ax.set_title(f"{train_name} ({operator_code})")
    else:
        ax.set_title(str(train_name))
    ax.set_xlabel("Time")
    ax.set_ylabel("Location")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()

    return fig
