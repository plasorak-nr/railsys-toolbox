"""Punctuality analysis helpers for Eval Manager arrival data."""

from datetime import timedelta

import polars as pl

from rsys_toolbox.core import filter_deadlocks, filter_zzztiplocs, selector_filter
from rsys_toolbox.io.data_types import EvalManagerData


@selector_filter()
def punctuality(
    data: EvalManagerData,
    group_by: list[str] = ["Station name", "Station abbreviation"],
    tolerance: timedelta = timedelta(minutes=1),
    remove_zzztiplocs: bool = True,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Calculate the share of arrivals within the punctuality tolerance.

    Args:
        data: Source Eval Manager dataframe.
        group_by: Column names to group punctuality by.
        tolerance: Maximum difference between actual and scheduled arrival for
            an event to count as punctual.
        remove_zzztiplocs: Whether to exclude rows where ``Station abbreviation``
            starts with ``ZZZ``. Defaults to True.
        exclude_deadlocks: When ``True``, remove simulations containing a
            deadlock. Defaults to ``True`` when both deadlock flags are ``None``.
        only_deadlocks: When ``True``, keep only simulations containing a
            deadlock. Mutually exclusive with ``exclude_deadlocks``.

    Returns:
        A dataframe grouped by ``group_by`` with a ``punctuality`` proportion.

    """
    data = filter_deadlocks(data, exclude_deadlocks=exclude_deadlocks, only_deadlocks=only_deadlocks)
    if remove_zzztiplocs:
        data = filter_zzztiplocs(data)
    tolerance_duration = pl.duration(seconds=int(tolerance.total_seconds()))

    return (
        data
        .group_by(group_by)
        .agg(
            ((pl.col("Actual arrival") - pl.col("Scheduled arrival")) <= tolerance_duration).cast(pl.Float32).mean().alias("punctuality"),
            pl.len().alias("punctuality_count"),
        )
        .filter(pl.col("punctuality").is_not_null())
        .with_columns(
            # Binomial standard error: SE = sqrt(p * (1 - p) / n)
            ((pl.col("punctuality") * (1 - pl.col("punctuality"))) / pl.col("punctuality_count")).sqrt().alias("punctuality_uncertainty"),
        )
    )
