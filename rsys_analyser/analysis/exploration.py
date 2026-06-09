from rsys_analyser.io.data_types import EvalManagerData
import polars as pl
from functools import wraps

def deadlock_selection(function):
    @wraps(function)
    def wrap(data: EvalManagerData, exclude_deadlocks: bool|None=None, only_deadlocks: bool|None=None, *args, **kwargs):
        if exclude_deadlocks and only_deadlocks:
            raise ValueError('Cannot have exclude_deadlocks and only_deadlocks valid at the same time')

        if exclude_deadlocks is None and only_deadlocks is None:
            exclude_deadlocks = True

        deadlock_sims = data.filter(pl.col('Deadlock')).get_column('Simulation no.').unique()

        if exclude_deadlocks:
            return function(
                data.filter(~pl.col('Simulation no.').is_in(deadlock_sims)),
                *args,
                **kwargs
            )


        if only_deadlocks:
            return function(
                data.filter(pl.col('Simulation no.').is_in(deadlock_sims)),
                *args,
                **kwargs
            )

        return function(data, *args, **kwargs)
    return wrap

@deadlock_selection
def get_valid_simulations(data: EvalManagerData) -> pl.Series:
    return data \
        .get_column('Simulation no.') \
        .unique() \
        .sort()


@deadlock_selection
def get_all_stations(data: EvalManagerData) -> pl.DataFrame:
    return data \
        .select(('Station abbreviation', 'Station name')) \
        .unique() \
        .sort(by='Station name')