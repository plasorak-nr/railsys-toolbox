"""Exploration helpers for inspecting evaluation-manager data.

The functions in this module provide small, composable dataframe queries for
common lookup and filtering tasks.
"""

import polars as pl

from rsys_toolbox.core import (
    deadlock_selection,
    extract_pattern,
    remove_zzztiplocs,
    selector_filter,
)
from rsys_toolbox.io.data_types import EvalManagerData


def _select_unique_sort(data: pl.DataFrame, select: str | tuple, sort_by: str | tuple | None = None) -> pl.DataFrame:
    """Select columns, drop duplicates, and sort the result.

    Args:
        data: Source dataframe.
        select: Column name or names to keep.
        sort_by: Column name or names to sort by. Defaults to the first
            selected column.

    Returns:
        A dataframe containing unique selected rows sorted by ``sort_by``.

    """
    select = (select,) if isinstance(select, str) else select

    if sort_by is None:
        sort_by = select[0]

    return data.select(select).unique().sort(sort_by)


@remove_zzztiplocs
@deadlock_selection
@extract_pattern
@selector_filter()
def search_events(
    data: EvalManagerData,
) -> pl.DataFrame:
    """Filter events by any combination of time, location, train, or selector.

    When no filters are provided, the full dataset is returned.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        The filtered dataframe.

    """
    return data


@deadlock_selection
def get_valid_simulations(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct simulation numbers present in the dataset.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe with unique values from ``Simulation no.``.

    """
    return _select_unique_sort(data, "Simulation no.")


@remove_zzztiplocs
@deadlock_selection
def get_all_stations(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct stations, ordered by station name.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe of station abbreviations and names.

    """
    return _select_unique_sort(data, ("Station abbreviation", "Station name"), "Station name")


@remove_zzztiplocs
@deadlock_selection
def get_all_lines_at_station(data: EvalManagerData, station: str) -> pl.DataFrame:
    """Return the distinct lines and tracks associated with a station.

    Args:
        data: Source Eval Manager dataframe.
        station: Station abbreviation or station name.

    Returns:
        A dataframe of unique line, route, and track combinations at the
        requested station.

    """
    df = data.filter((pl.col("Station abbreviation") == station) | (pl.col("Station name") == station))
    return _select_unique_sort(df, ("Station abbreviation", "Station name", "Line abbr.", "Route", "Scheduled track"), ("Station name", "Route"))


@deadlock_selection
@extract_pattern
def get_all_operator_codes(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct operator codes present in the dataset.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe with unique operator codes.

    """
    return _select_unique_sort(data, "Operator Code")


@deadlock_selection
@extract_pattern
def get_all_service_codes(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct service codes present in the dataset.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe with unique service codes.

    """
    return _select_unique_sort(data, "Service Code")


@deadlock_selection
@extract_pattern
def get_all_patterns(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct pattern values present in the dataset.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe with unique pattern values.

    """
    return _select_unique_sort(data, "Pattern")


@deadlock_selection
@extract_pattern
def get_all_train_numbers(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct train numbers present in the dataset.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe with unique train numbers.

    """
    return _select_unique_sort(data, "Train no.")


@deadlock_selection
@extract_pattern
def get_all_train_names(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct train names present in the dataset.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe with unique train names.

    """
    return _select_unique_sort(data, "Train name")


@deadlock_selection
@extract_pattern
def get_all_train_classes(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct train classes present in the dataset.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe with unique train classes.

    """
    return _select_unique_sort(data, "Train class")


@deadlock_selection
@extract_pattern
def get_all_train_categories(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct train categories present in the dataset.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe with unique train categories.

    """
    return _select_unique_sort(data, "Train category")


@deadlock_selection
@extract_pattern
def get_all_train_formations(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct train formation IDs present in the dataset.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe with unique train formation IDs.

    """
    return _select_unique_sort(data, "Train formation ID", "Train formation ID")


@remove_zzztiplocs
@deadlock_selection
@selector_filter()
def dump_train(
    data: EvalManagerData,
    simulation: int,
) -> pl.DataFrame:
    """Create a log of a train's journey through one simulation.

    Shows all stations and routes the train visits, along with scheduled and
    actual arrival/departure times. Raises an error if the filter matches
    zero or more than one train.

    Args:
        data: Source Eval Manager dataframe.
        simulation: Simulation number to filter by.

    Returns:
        A dataframe with one row per station stop, sorted by station order,
        containing: Station abbreviation, Station name, Route, Scheduled arrival,
        Actual arrival, Scheduled departure, Actual departure.

    Raises:
        ValueError: If the filters match zero or more than one train.

    """
    df = data.filter(pl.col("Simulation no.") == simulation)

    # Validate that exactly one train is matched
    unique_trains = df.select(("Train no.", "Train name")).unique()
    if unique_trains.is_empty():
        msg = f"No train found matching filter in simulation {simulation}"
        raise ValueError(msg)
    if len(unique_trains) > 1:
        msg = f"Multiple trains matched filter in simulation {simulation}: {unique_trains}"
        raise ValueError(msg)

    return df.select(
        "Station index",
        "Station abbreviation",
        "Station name",
        "Route",
        "Scheduled arrival",
        "Actual arrival",
        "SchedDep",
        "Actual departure",
    ).sort("Station index")
