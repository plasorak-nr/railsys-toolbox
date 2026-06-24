"""Typed dataframe aliases used by the IO layer."""

from pathlib import Path

import polars as pl


class EvalManagerData(pl.DataFrame):
    """Polars dataframe subtype for Eval Manager datasets."""
    pass