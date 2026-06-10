import operator
from datetime import timedelta
from functools import reduce

import polars as pl

from rsys_analyser.core import CombinedSelector, LocationSelector, TimeSelector, TrainSelector, deadlock_selection, extract_pattern
from rsys_analyser.io.data_types import EvalManagerData


def _correlation(data: pl.DataFrame, cause_expr: pl.Expr, effect_expr: pl.Expr, max_cause_window: timedelta | None = None) -> pl.DataFrame:
    df_cause = data.filter(cause_expr)
    df_effect = data.filter(effect_expr)

    cause_renamed = df_cause.rename({c: f"{c}_cause" for c in df_cause.columns})
    effect_renamed = df_effect.with_row_index("_effect_idx").rename({c: f"{c}_effect" for c in df_effect.columns})

    base_time_filter = pl.col("Actual departure_cause") < pl.col("Actual departure_effect")
    window_filter = (pl.col("Actual departure_effect") - pl.col("Actual departure_cause")) <= max_cause_window if max_cause_window is not None else None

    return (
        effect_renamed.join(cause_renamed, left_on="Simulation no._effect", right_on="Simulation no._cause", how="inner")
        .filter(
            base_time_filter if window_filter is None else (base_time_filter & window_filter),
        )
        .sort("Actual departure_cause", descending=True)
        .unique(subset=["_effect_idx"], keep="first")
        .drop("_effect_idx")
    )



@deadlock_selection
@extract_pattern
def correlation(
    data: EvalManagerData,
    combined_cause_hypothesis: CombinedSelector | None = None,
    combined_effect_hypothesis: CombinedSelector | None = None,
    location_cause_hypothesis: LocationSelector | None = None,
    location_effect_hypothesis: LocationSelector | None = None,
    time_cause_hypothesis: TimeSelector | None = None,
    time_effect_hypothesis: TimeSelector | None = None,
    train_cause_hypothesis: TrainSelector | None = None,
    train_effect_hypothesis: TrainSelector | None = None,
    max_cause_window: timedelta | None = None,
) -> pl.DataFrame:

    cause_expr = []
    if combined_cause_hypothesis:
        cause_expr += [combined_cause_hypothesis.get_filter()]
    if location_cause_hypothesis:
        cause_expr += [location_cause_hypothesis.get_filter()]
    if time_cause_hypothesis:
        cause_expr += [time_cause_hypothesis.get_filter()]
    if train_cause_hypothesis:
        cause_expr += [train_cause_hypothesis.get_filter()]

    if not cause_expr:
        msg = "There was no cause selector setup"
        raise RuntimeError(msg)

    cause_expr = reduce(operator.and_, cause_expr)

    effect_expr = []
    if combined_effect_hypothesis:
        effect_expr += [combined_effect_hypothesis.get_filter()]
    if location_effect_hypothesis:
        effect_expr += [location_effect_hypothesis.get_filter()]
    if time_effect_hypothesis:
        effect_expr += [time_effect_hypothesis.get_filter()]
    if train_effect_hypothesis:
        effect_expr += [train_effect_hypothesis.get_filter()]

    if not effect_expr:
        msg = "There was no effect selector setup"
        raise RuntimeError(msg)

    effect_expr = reduce(operator.and_, effect_expr)

    return _correlation(data, cause_expr=cause_expr, effect_expr=effect_expr, max_cause_window=max_cause_window)
