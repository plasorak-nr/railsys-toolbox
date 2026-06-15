"""Load Eval Manager CSV exports into the package's typed dataframe wrapper."""

from logging import getLogger
from pathlib import Path
from typing import cast

import polars as pl

from rsys_toolbox.io.data_types import EvalManagerData
from rsys_toolbox.io.eval_manager_format import SCHEMA_EVAL_MANAGER_POLARS

logger = getLogger("eval_manager")


def load(file: Path | str) -> EvalManagerData:
    """Read an Eval Manager export, normalize its columns, and return typed data.

    Args:
        file: Path to the Eval Manager CSV export.

    Returns:
        The normalized Eval Manager dataframe.

    """
    df = pl.read_csv(file, separator="|", schema=SCHEMA_EVAL_MANAGER_POLARS)

    df = df.filter(~pl.col("Simulation no.").is_in(["Average simulations", "No simulation data available"]))

    df = df.cast({"Simulation no.": pl.Int32, "Deadlock": pl.Boolean, "Replatforming": pl.Boolean, "Change of direction of travel": pl.Boolean})

    return cast("EvalManagerData", df)
