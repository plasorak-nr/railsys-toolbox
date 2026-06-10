"""Exploration helpers for inspecting evaluation-manager data.

The functions in this module provide small, composable dataframe queries for
common lookup and filtering tasks.
"""

from functools import reduce
from operator import and_

import polars as pl

from rsys_analyser.core import (
    CombinedSelector,
    LocationSelector,
    TimeSelector,
    TrainSelector,
    deadlock_selection,
    extract_pattern,
)
from rsys_analyser.io.data_types import EvalManagerData


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


@deadlock_selection
@extract_pattern
def search_events(
    data: EvalManagerData,
    time_filter: TimeSelector | None = None,
    location_filter: LocationSelector | None = None,
    train_filter: TrainSelector | None = None,
    selector: CombinedSelector | None = None,
) -> pl.DataFrame:
    """Filter events by any combination of time, location, train, or selector.

    When no filters are provided, the full dataset is returned.

    Args:
        data: Source Eval Manager dataframe.
        time_filter: Optional time-based selector.
        location_filter: Optional location-based selector.
        train_filter: Optional train-based selector.
        selector: Optional combined selector.

    Returns:
        The filtered dataframe.

    """
    filters = []

    if time_filter:
        filters += [time_filter.get_filter()]
    if location_filter:
        filters += [location_filter.get_filter()]
    if train_filter:
        filters += [train_filter.get_filter()]
    if selector:
        filters += [selector.get_filter()]
    if not filters:
        filters += [pl.lit(True)]

    return data.filter(reduce(and_, filters))


@deadlock_selection
def get_valid_simulations(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct simulation numbers present in the dataset.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe with unique values from ``Simulation no.``.

    """
    return _select_unique_sort(data, "Simulation no.")


@deadlock_selection
def get_all_stations(data: EvalManagerData) -> pl.DataFrame:
    """Return the distinct stations, ordered by station name.

    Args:
        data: Source Eval Manager dataframe.

    Returns:
        A dataframe of station abbreviations and names.

    """
    return _select_unique_sort(data, ("Station abbreviation", "Station name"), "Station name")


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
