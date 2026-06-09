from rsys_analyser.io.data_types import EvalManagerData
from rsys_analyser.core import (
    deadlock_selection,
    extract_pattern,
    TimeSelector,
    LocationSelector,
    TrainSelector,
    CombinedSelector,
)

import polars as pl

from functools import reduce
from operator import and_

def _select_unique_sort(data: pl.DataFrame, select:str|tuple, sort_by:str|tuple|None=None) -> pl.DataFrame:
    select = (select,) if isinstance(select, str) else select

    if sort_by is None:
        sort_by=select[0]

    return data.select(select).unique().sort(sort_by)


@deadlock_selection
@extract_pattern
def search_events(
        data: EvalManagerData,
        time_filter: TimeSelector | None = None,
        location_filter: LocationSelector | None = None,
        train_filter: TrainSelector | None = None,
        selector: CombinedSelector | None = None,
    ):

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
    return _select_unique_sort(data, 'Simulation no.')


@deadlock_selection
def get_all_stations(data: EvalManagerData) -> pl.DataFrame:
    return _select_unique_sort(data, ('Station abbreviation', 'Station name'), 'Station name')


@deadlock_selection
def get_all_lines_at_station(data: EvalManagerData, station: str) -> pl.DataFrame:
    df = data.filter((pl.col('Station abbreviation') == station) | (pl.col('Station name') == station))
    return _select_unique_sort(df, ('Station abbreviation', 'Station name', 'Line abbr.', 'Route', 'Scheduled track'), ('Station name', 'Route'))


@deadlock_selection
@extract_pattern
def get_all_operator_codes(data: EvalManagerData) -> pl.DataFrame:
    return _select_unique_sort(data, 'Operator Code')


@deadlock_selection
@extract_pattern
def get_all_service_codes(data: EvalManagerData) -> pl.DataFrame:
    return _select_unique_sort(data, 'Service Code')


@deadlock_selection
@extract_pattern
def get_all_patterns(data: EvalManagerData) -> pl.DataFrame:
    return _select_unique_sort(data, 'Pattern')


@deadlock_selection
@extract_pattern
def get_all_train_numbers(data: EvalManagerData) -> pl.DataFrame:
    return _select_unique_sort(data, 'Train no.')


@deadlock_selection
@extract_pattern
def get_all_train_names(data: EvalManagerData) -> pl.DataFrame:
    return _select_unique_sort(data, 'Train name')


@deadlock_selection
@extract_pattern
def get_all_train_classes(data: EvalManagerData) -> pl.DataFrame:
    return _select_unique_sort(data, 'Train class')


@deadlock_selection
@extract_pattern
def get_all_train_categories(data: EvalManagerData) -> pl.DataFrame:
    return _select_unique_sort(data, 'Train category')


@deadlock_selection
@extract_pattern
def get_all_train_formations(data: EvalManagerData) -> pl.DataFrame:
    return _select_unique_sort(data, 'Train formation ID', 'Train formation ID')

