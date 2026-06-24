"""Punctuality analysis helpers for Eval Manager arrival data."""

from datetime import timedelta

import polars as pl

from rsys_toolbox.core import deadlock_selection, extract_pattern, remove_zzztiplocs, selector_filter
from rsys_toolbox.io.data_types import EvalManagerData


@remove_zzztiplocs
@deadlock_selection
@extract_pattern
@selector_filter()
def punctuality(
    data: EvalManagerData,
    group_by: list[str] = ["Station name"],
    tolerance: timedelta = timedelta(minutes=1),
) -> pl.DataFrame:
    """Calculate the share of arrivals within the punctuality tolerance.

    Args:
        data: Source Eval Manager dataframe.
        group_by: Column names to group punctuality by.
        tolerance: Maximum difference between actual and scheduled arrival for
            an event to count as punctual.

    Returns:
        A dataframe grouped by ``group_by`` with a ``punctuality`` proportion.

    """
    tolerance_duration = pl.duration(seconds=int(tolerance.total_seconds()))

    return data.group_by(group_by).agg(
        ((pl.col("Actual arrival") - pl.col("Scheduled arrival")) <= tolerance_duration).cast(pl.Float32).mean().alias("punctuality")
    )
