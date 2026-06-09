import polars as pl

pl.Config.set_tbl_rows(200)  # show up to 100 rows
import logging
from pathlib import Path

import typer

logger = logging.getLogger("rsys-analyser")
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

app = typer.Typer()


@app.command()
def main(file: Path) -> None:
    df = pl.read_csv(
        file,
        separator="|",
        infer_schema_length=10_000,
    )
    logger.info(df.columns)
    logger.info(df.select("Station name").unique().sort("Station name"))
    logger.info(df.select("StopType").unique().sort("StopType"))
    logger.info(df.filter(pl.col("Station name") == "Barnt Green").group_by("Simulation no.").agg(pl.count().alias("n_trains")))
    logger.info(df.filter(pl.col("Station name") == "Barnt Green").group_by("Pattern").agg(pl.count().alias("n_trains")))

    logger.info(
        df.filter(
            (pl.col("Station name") == "Barnt Green")
            & ((pl.col("Scheduled track") == "BGRN T-2") | ((pl.col("Scheduled track") != "BGRN T-2") & (pl.col("Pattern")))),
        )
        .select("Scheduled track", "Actual track")
        .unique(),
    )
    # df.with_columns(pl.col("a").cast(pl.Float64))
