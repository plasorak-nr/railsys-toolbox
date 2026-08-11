"""Punctuality analysis helpers for Eval Manager arrival data."""

from datetime import timedelta

import polars as pl

from rsys_toolbox.core import deadlock_selection, extract_pattern, filter_zzztiplocs, selector_filter
from rsys_toolbox.io.data_types import EvalManagerData


@deadlock_selection
@extract_pattern
@selector_filter()
def punctuality(
    data: EvalManagerData,
    group_by: list[str] = ["Station name", "Station abbreviation"],
    tolerance: timedelta = timedelta(minutes=1),
    remove_zzztiplocs: bool = True,
) -> pl.DataFrame:
    """Calculate the share of arrivals within the punctuality tolerance.

    Args:
        data: Source Eval Manager dataframe.
        group_by: Column names to group punctuality by.
        tolerance: Maximum difference between actual and scheduled arrival for
            an event to count as punctual.
        remove_zzztiplocs: Whether to exclude rows where ``Station abbreviation``
            starts with ``ZZZ``. Defaults to True.

    Returns:
        A dataframe grouped by ``group_by`` with a ``punctuality`` proportion.

    """
    if remove_zzztiplocs:
        data = filter_zzztiplocs(data)
    tolerance_duration = pl.duration(seconds=int(tolerance.total_seconds()))

    return (
        data.group_by(group_by).agg(
            ((pl.col("Actual arrival") - pl.col("Scheduled arrival")) <= tolerance_duration).cast(pl.Float32).mean().alias("punctuality"),
            pl.len().alias("punctuality_count"),
        )
        .filter(pl.col("punctuality").is_not_null())
        .with_columns(
            # Binomial standard error: SE = sqrt(p * (1 - p) / n)
            ((pl.col("punctuality") * (1 - pl.col("punctuality"))) / pl.col("punctuality_count")).sqrt().alias("punctuality_uncertainty"),
        )
    )

