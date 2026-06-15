"""Causality investigation helpers for correlating likely causes and effects."""

import operator
from datetime import timedelta
from functools import reduce
from rich.progress import track
import polars as pl

from rsys_toolbox.core import CombinedSelector, LocationSelector, TimeSelector, TrainSelector, deadlock_selection, extract_pattern, remove_zzztiplocs

from rsys_toolbox.io.data_types import EvalManagerData


def _correlation(data: pl.DataFrame, cause_expr: pl.Expr, effect_expr: pl.Expr, max_cause_window: timedelta | None = None) -> pl.DataFrame:
    """Join cause and effect rows and keep the closest valid cause for each effect.

    Args:
        data: Source dataframe containing potential causes and effects.
        cause_expr: Boolean Polars expression selecting cause rows.
        effect_expr: Boolean Polars expression selecting effect rows.
        max_cause_window: Optional maximum time between cause and effect.

    Returns:
        A dataframe where each effect row is paired with its most recent valid
        cause row within the same simulation.

    """
    df_cause = data.filter(cause_expr)
    df_effect = data.filter(effect_expr)

    if df_cause.is_empty():
        raise RuntimeError('Your cause selectors lead to no events!')

    if df_effect.is_empty():
        raise RuntimeError('Your effect selectors lead to no events!')

    cause_renamed = df_cause.rename({c: f"{c}_cause" for c in df_cause.columns})
    effect_renamed = df_effect.with_row_index("_effect_idx").rename({c: f"{c}_effect" for c in df_effect.columns})

    base_time_filter = pl.col("Actual departure_cause") < pl.col("Actual departure_effect")
    window_filter = (pl.col("Actual departure_effect") - pl.col("Actual departure_cause")) <= max_cause_window if max_cause_window is not None else None

    return (
        effect_renamed
        .join(cause_renamed, left_on="Simulation no._effect", right_on="Simulation no._cause", how="inner")
        .filter(
            base_time_filter if window_filter is None else (base_time_filter & window_filter),
        )
        .sort("Actual departure_cause", descending=True)
        .unique(subset=["_effect_idx"], keep="first")
        .drop("_effect_idx")
    )


@remove_zzztiplocs
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
    max_cause_window: timedelta | None = timedelta(minutes=5),
) -> pl.DataFrame:
    """Correlate candidate causes with effects using the configured selectors.

    Args:
        data: Source Eval Manager dataframe.
        combined_cause_hypothesis: Optional combined selector for causes.
        combined_effect_hypothesis: Optional combined selector for effects.
        location_cause_hypothesis: Optional location selector for causes.
        location_effect_hypothesis: Optional location selector for effects.
        time_cause_hypothesis: Optional time selector for causes.
        time_effect_hypothesis: Optional time selector for effects.
        train_cause_hypothesis: Optional train selector for causes.
        train_effect_hypothesis: Optional train selector for effects.
        max_cause_window: Optional maximum time between cause and effect.

    Returns:
        A dataframe of effect rows matched to candidate cause rows.

    Raises:
        RuntimeError: If no cause selector or no effect selector is provided.

    """
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


@remove_zzztiplocs
@deadlock_selection
@extract_pattern
def correlation_search(
    data: EvalManagerData,
    combined_cause_hypothesis: CombinedSelector | None = None,
    combined_effect_hypothesis: CombinedSelector | None = None,
    location_cause_hypothesis: LocationSelector | None = None,
    location_effect_hypothesis: LocationSelector | None = None,
    time_cause_hypothesis: TimeSelector | None = None,
    time_effect_hypothesis: TimeSelector | None = None,
    train_cause_hypothesis: TrainSelector | None = None,
    train_effect_hypothesis: TrainSelector | None = None,
    max_cause_window: timedelta | None = timedelta(minutes=5),
) -> pl.DataFrame:
    """Search for candidate cause events and score their correlation to effects.

    This scans all events that occur before selected effects (and optionally
    within ``max_cause_window``), runs ``_correlation`` for each unique event
    metadata signature, and returns one row per candidate with summary metrics.

    Args:
        data: Source Eval Manager dataframe.
        combined_cause_hypothesis: Optional combined selector for causes.
        combined_effect_hypothesis: Optional combined selector for effects.
        location_cause_hypothesis: Optional location selector for causes.
        location_effect_hypothesis: Optional location selector for effects.
        time_cause_hypothesis: Optional time selector for causes.
        time_effect_hypothesis: Optional time selector for effects.
        train_cause_hypothesis: Optional train selector for causes.
        train_effect_hypothesis: Optional train selector for effects.
        max_cause_window: Optional maximum time between cause and effect.

    Returns:
        A dataframe with candidate cause metadata and correlation metrics.

    Raises:
        RuntimeError: If no effect selector is provided.

    """

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
        cause_expr = [pl.lit(True)]

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

    cause_metadata_cols = [
        "Station abbreviation",
        "Station name",
        "Line abbr.",
        "Route",
        "Scheduled track",
        "Pattern",
        "Train no.",
        "Train name",
        "Train class",
        "Train formation ID",
        "Operator Code",
        "Service Code",
        "Origin TIPLOC",
        "Destination TIPLOC",
    ]

    df_effect = data.filter(effect_expr)
    df_cause = data.filter(cause_expr)

    if df_effect.is_empty():
        raise RuntimeError('Your effect selectors lead to no events!')

    df_effect_scan = df_effect.select(
        pl.col("Simulation no.").alias("Simulation no._effect"),
        pl.col("Actual departure").alias("Actual departure_effect"),
        pl.col("Train name").alias("Train name_effect"),
    )

    candidate_pairs = (
        df_cause.select(
            pl.all(),
            pl.col("Simulation no.").alias("Simulation no._cause"),
            pl.col("Actual departure").alias("Actual departure_cause"),
        )
        .join(df_effect_scan, left_on="Simulation no._cause", right_on="Simulation no._effect", how="inner")
        .filter(
            (pl.col("Actual departure_cause") < pl.col("Actual departure_effect"))
            & (pl.col("Train name") != pl.col("Train name_effect"))
        )
    )
    if max_cause_window is not None:
        candidate_pairs = candidate_pairs.filter((pl.col("Actual departure_effect") - pl.col("Actual departure_cause")) <= max_cause_window)

    candidate_metadata = candidate_pairs.select([col for col in cause_metadata_cols if col in candidate_pairs.columns]).unique()

    if candidate_metadata.is_empty():
        return pl.DataFrame(
            schema={
                **{col: data.schema[col] for col in cause_metadata_cols if col in data.columns},
                "pair_count": pl.UInt32,
                "simulation_count": pl.UInt32,
                "correlation": pl.Float64,
            },
        )

    results: list[dict[str, object]] = []
    for candidate in track(candidate_metadata.to_dicts(), 'Looping over all possible causes...'):
        candidate_filter = [pl.col(col) == value for col, value in candidate.items()]

        if not candidate_filter:
            continue

        matched = _correlation(
            data,
            cause_expr=reduce(operator.and_, candidate_filter),
            effect_expr=effect_expr,
            max_cause_window=max_cause_window,
        )

        if matched.is_empty() or (matched.count().rows()[0][0] < 10):
            continue


        with_delays = matched.with_columns(
            (pl.col("Actual departure_cause") - pl.col("SchedDep_cause")).dt.total_seconds().alias("lateness_cause"),
            (pl.col("Actual departure_effect") - pl.col("SchedDep_effect")).dt.total_seconds().alias("lateness_effect"),
        ).filter((pl.col("lateness_cause") > 0) & (pl.col("lateness_effect") > 0))

        metrics = with_delays.select(
            pl.len().alias("pair_count"),
            pl.n_unique("Simulation no._effect").alias("simulation_count"),
            pl.corr("lateness_cause", "lateness_effect").alias("correlation"),
        ).row(0, named=True)

        results.append({**candidate, **metrics})

    if not results:
        return pl.DataFrame(
            schema={
                **{col: data.schema[col] for col in cause_metadata_cols if col in data.columns},
                "pair_count": pl.UInt32,
                "simulation_count": pl.UInt32,
                "correlation": pl.Float64,
            },
        )

    return pl.DataFrame(results).sort("correlation", descending=True, nulls_last=True)


