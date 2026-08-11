"""Exploration helpers for inspecting evaluation-manager data.

The functions in this module provide small, composable dataframe queries for
common lookup and filtering tasks.
"""

import polars as pl

from rsys_toolbox.core import (
    CombinedSelector,
    LocationSelector,
    TimeSelector,
    TrainSelector,
    apply_selector_filter,
    filter_deadlocks,
    filter_zzztiplocs,
)


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


def search_events(
    data: pl.DataFrame,
    remove_zzztiplocs: bool = True,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
    combined_selector: CombinedSelector | None = None,
    location_selector: LocationSelector | None = None,
    time_selector: TimeSelector | None = None,
    train_selector: TrainSelector | None = None,
    data_filter: pl.Expr | None = None,
) -> pl.DataFrame:
    """Filter events by any combination of time, location, train, or selector.

    When no filters are provided, the full dataset is returned.

    Args:
        data: Source Eval Manager dataframe.
        remove_zzztiplocs: Whether to exclude rows where ``Station abbreviation``
            starts with ``ZZZ``. Defaults to True.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.
        combined_selector: Optional combined train/location/time selector.
        location_selector: Optional location selector.
        time_selector: Optional time selector.
        train_selector: Optional train selector.
        data_filter: Optional raw Polars expression applied before selectors.

    Returns:
        The filtered dataframe.

    """
    data = apply_selector_filter(
        data,
        combined_selector=combined_selector,
        location_selector=location_selector,
        time_selector=time_selector,
        train_selector=train_selector,
        data_filter=data_filter,
    )
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    if remove_zzztiplocs:
        data = filter_zzztiplocs(data)
    return data


def get_valid_simulations(
    data: pl.DataFrame,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct simulation numbers present in the dataset.

    Args:
        data: Source Eval Manager dataframe.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe with unique values from ``Simulation no.``.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    return _select_unique_sort(data, "Simulation no.")


def get_all_stations(
    data: pl.DataFrame,
    remove_zzztiplocs: bool = True,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct stations, ordered by station name.

    Args:
        data: Source Eval Manager dataframe.
        remove_zzztiplocs: Whether to exclude rows where ``Station abbreviation``
            starts with ``ZZZ``. Defaults to True.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe of station abbreviations and names.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    if remove_zzztiplocs:
        data = filter_zzztiplocs(data)
    return _select_unique_sort(data, ("Station abbreviation", "Station name"), "Station name")


def get_all_lines_at_station(
    data: pl.DataFrame,
    station: str,
    remove_zzztiplocs: bool = True,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct lines and tracks associated with a station.

    Args:
        data: Source Eval Manager dataframe.
        station: Station abbreviation or station name.
        remove_zzztiplocs: Whether to exclude rows where ``Station abbreviation``
            starts with ``ZZZ``. Defaults to True.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe of unique line, route, and track combinations at the
        requested station.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    if remove_zzztiplocs:
        data = filter_zzztiplocs(data)
    df = data.filter((pl.col("Station abbreviation") == station) | (pl.col("Station name") == station))
    return _select_unique_sort(df, ("Station abbreviation", "Station name", "Line abbr.", "Route", "Scheduled track"), ("Station name", "Route"))


def get_all_operator_codes(
    data: pl.DataFrame,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct operator codes present in the dataset.

    Args:
        data: Source Eval Manager dataframe.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe with unique operator codes.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    return _select_unique_sort(data, "Operator Code")


def get_all_service_codes(
    data: pl.DataFrame,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct service codes present in the dataset.

    Args:
        data: Source Eval Manager dataframe.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe with unique service codes.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    return _select_unique_sort(data, "Service Code")


def get_all_patterns(
    data: pl.DataFrame,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct pattern values present in the dataset.

    Args:
        data: Source Eval Manager dataframe.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe with unique pattern values.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    return _select_unique_sort(data, "Pattern")


def get_all_train_numbers(
    data: pl.DataFrame,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct train numbers present in the dataset.

    Args:
        data: Source Eval Manager dataframe.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe with unique train numbers.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    return _select_unique_sort(data, "Train no.")


def get_all_train_names(
    data: pl.DataFrame,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct train names present in the dataset.

    Args:
        data: Source Eval Manager dataframe.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe with unique train names.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    return _select_unique_sort(data, "Train name")


def get_all_train_classes(
    data: pl.DataFrame,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct train classes present in the dataset.

    Args:
        data: Source Eval Manager dataframe.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe with unique train classes.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    return _select_unique_sort(data, "Train class")


def get_all_train_categories(
    data: pl.DataFrame,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct train categories present in the dataset.

    Args:
        data: Source Eval Manager dataframe.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe with unique train categories.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    return _select_unique_sort(data, "Train category")


def get_all_train_formations(
    data: pl.DataFrame,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Return the distinct train formation IDs present in the dataset.

    Args:
        data: Source Eval Manager dataframe.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe with unique train formation IDs.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    return _select_unique_sort(data, "Train formation ID", "Train formation ID")


def dump_train(
    data: pl.DataFrame,
    simulation: int,
    remove_zzztiplocs: bool = True,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
    combined_selector: CombinedSelector | None = None,
    location_selector: LocationSelector | None = None,
    time_selector: TimeSelector | None = None,
    train_selector: TrainSelector | None = None,
    data_filter: pl.Expr | None = None,
) -> pl.DataFrame:
    """Create a log of a train's journey through one simulation.

    Shows all stations and routes the train visits, along with scheduled and
    actual arrival/departure times. Raises an error if the filter matches
    zero or more than one train.

    Args:
        data: Source Eval Manager dataframe.
        simulation: Simulation number to filter by.
        remove_zzztiplocs: Whether to exclude rows where ``Station abbreviation``
            starts with ``ZZZ``. Defaults to True.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.
        combined_selector: Optional combined train/location/time selector.
        location_selector: Optional location selector.
        time_selector: Optional time selector.
        train_selector: Optional train selector.
        data_filter: Optional raw Polars expression applied before selectors.

    Returns:
        A dataframe with one row per station stop, sorted by station order, containing:
        Station abbreviation, Station name, Route, Scheduled arrival,
        Actual arrival, Scheduled departure, Actual departure.

    Raises:
        ValueError: If the filters match zero or more than one train.

    """
    data = apply_selector_filter(
        data,
        combined_selector=combined_selector,
        location_selector=location_selector,
        time_selector=time_selector,
        train_selector=train_selector,
        data_filter=data_filter,
    )
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    if remove_zzztiplocs:
        data = filter_zzztiplocs(data)
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
