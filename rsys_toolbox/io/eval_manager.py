"""Load Eval Manager CSV exports into the package's typed dataframe wrapper."""

from logging import getLogger
from pathlib import Path

import polars as pl

from rsys_toolbox.io.data_types import EvalManagerData
from rsys_toolbox.io.eval_manager_format import SCHEMA_EVAL_MANAGER_POLARS

logger = getLogger("eval_manager")

_TIME_COLUMNS = ("Scheduled arrival", "Actual arrival", "SchedDep", "Actual departure")


def load(file: Path | str) -> EvalManagerData:
    """Read an Eval Manager export, normalize its columns, and return typed data.

    Args:
        file: Path to the Eval Manager CSV export.

    Returns:
        The normalized Eval Manager dataframe.

    """
    # Read time columns as strings first to tolerate placeholder values such as
    # "??:??:??" that appear in some exports, then parse them leniently.
    schema_relaxed = {col: (pl.String if dtype == pl.Time else dtype) for col, dtype in SCHEMA_EVAL_MANAGER_POLARS.items()}
    df = pl.read_csv(file, separator="|", schema=schema_relaxed)

    df = df.filter(~pl.col("Simulation no.").is_in(["Average simulations", "No simulation data available"]))

    df = df.cast({"Simulation no.": pl.Int32, "Deadlock": pl.Boolean, "Replatforming": pl.Boolean, "Change of direction of travel": pl.Boolean})

    # Parse time columns, converting invalid/placeholder strings to null.
    df = df.with_columns([pl.col(col).str.to_time("%H:%M:%S", strict=False).alias(col) for col in _TIME_COLUMNS if col in df.columns])

    return EvalManagerData(df)
