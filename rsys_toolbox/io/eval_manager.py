"""Load Eval Manager CSV exports into the package's typed dataframe wrapper."""

from logging import getLogger
from pathlib import Path

import polars as pl

from rsys_toolbox.io.data_types import EvalManagerData
from rsys_toolbox.io.eval_manager_format import SCHEMA_EVAL_MANAGER_POLARS

logger = getLogger("eval_manager")

_TIME_COLUMNS = ("Scheduled arrival", "Actual arrival", "SchedDep", "Actual departure")


def _extract_pattern_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Parse the ``Pattern`` column into operator, service, origin, and destination columns.

    Two pattern formats are auto-detected per row:

    - ``/Operator/ServiceCode/Origin/Destination`` (``/EX/21381901/OOCINT/SHENFLD``)
    - ``/Operator/ServiceCode/Origin-Destination`` ()``/WA/52407530/SOTD107-KNGSBCE``)

    Args:
        df: Dataframe containing a ``Pattern`` column.

    Returns:
        The dataframe with four additional columns: ``Operator Code``, ``Service Code``,
        ``Origin TIPLOC``, and ``Destination TIPLOC``.

    Raises:
        ValueError: If any row's ``Pattern`` value does not match a recognised format.

    """
    _re_slashes = r"^/([^/]+)/([^/]+)/([^/\-]+)/([^/\-]+)$"  # format 1: four slash-segments
    _re_dash    = r"^/([^/]+)/([^/]+)/([^/\-]+)-([^/\-]+)$"  # format 2: dash-joined origin-dest

    p = pl.col("Pattern")
    is_fmt1 = p.str.contains(_re_slashes)
    is_known = is_fmt1 | p.str.contains(_re_dash)

    unrecognised = df.filter(~is_known).get_column("Pattern").unique().to_list()
    if unrecognised:
        msg = f"Unrecognised Pattern values (expected /Op/Svc/Origin/Dest or /Op/Svc/Origin-Dest): {unrecognised}"
        raise ValueError(msg)

    return df.with_columns(
        pl.when(is_fmt1)
          .then(p.str.extract(_re_slashes, group_index=1))
          .otherwise(p.str.extract(_re_dash, group_index=1))
          .alias("Operator Code"),

        pl.when(is_fmt1)
          .then(p.str.extract(_re_slashes, group_index=2))
          .otherwise(p.str.extract(_re_dash, group_index=2))
          .alias("Service Code"),

        pl.when(is_fmt1)
          .then(p.str.extract(_re_slashes, group_index=3))
          .otherwise(p.str.extract(_re_dash, group_index=3))
          .alias("Origin TIPLOC"),

        pl.when(is_fmt1)
          .then(p.str.extract(_re_slashes, group_index=4))
          .otherwise(p.str.extract(_re_dash, group_index=4))
          .alias("Destination TIPLOC"),
    )


def load(file: Path | str) -> EvalManagerData:
    """Read an Eval Manager export, normalize its columns, and return typed data.

    The ``Pattern`` column is parsed into ``Operator Code``, ``Service Code``,
    ``Origin TIPLOC``, and ``Destination TIPLOC`` columns on load.

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

    # Extract structured fields from the Pattern column.
    df = _extract_pattern_columns(df)

    return EvalManagerData(df)
