from rsys_toolbox.core import CombinedSelector, LocationSelector, TimeSelector, TrainSelector, deadlock_selection, extract_pattern, remove_zzztiplocs
from rsys_toolbox.io.data_types import EvalManagerData

from datetime import timedelta
import polars as pl
from functools import reduce
import operator

@remove_zzztiplocs
@deadlock_selection
@extract_pattern
def punctuality(
    data: EvalManagerData,
    combined_selector: CombinedSelector | None = None,
    location_selector: LocationSelector | None = None,
    time_selector: TimeSelector | None = None,
    train_selector: TrainSelector | None = None,
    group_by: list[str] = ['Station name'],
    tolerance: timedelta = timedelta(minutes=1)
) -> pl.DataFrame:

    expr = []
    if combined_selector:
        expr += [combined_selector.get_filter()]
    if location_selector:
        expr += [location_selector.get_filter()]
    if time_selector:
        expr += [time_selector.get_filter()]
    if train_selector:
        expr += [train_selector.get_filter()]
    if not expr:
        expr = [pl.lit(True)]

    expr = reduce(operator.and_, expr)
    tolerance_duration = pl.duration(seconds=int(tolerance.total_seconds()))

    return data.filter(expr).group_by(group_by).agg(
        (
            (pl.col('Actual arrival') - pl.col('Scheduled arrival'))
            <= tolerance_duration
        )
        .cast(pl.Float32)
        .mean()
        .alias('punctuality')
    )
