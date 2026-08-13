"""Correlation bar-chart plotting utilities."""

import matplotlib.pyplot as plt
import polars as pl
from matplotlib.figure import Figure


def plot_correlation_bars(
    data: pl.DataFrame,
    title: str = "Delay candidate causes",
    min_pair_count: int = 10,
) -> Figure:
    """Plot a bar chart of correlation coefficients from a ``correlation_search`` result.

    Filters out null correlations and rows with fewer than ``min_pair_count``
    observation pairs, then sorts by descending correlation before plotting.
    Error bars show the ``correlation_uncertainty`` column.

    Args:
        data: Output dataframe from :func:`rsys_toolbox.analysis.correlation_search`.
        title: Title for the plot.
        min_pair_count: Minimum number of observation pairs required to include
            a candidate cause. Defaults to 10.

    Returns:
        A matplotlib Figure containing the correlation bar chart.

    Raises:
        ValueError: If required columns are missing or no rows remain after filtering.

    """
    required = {"correlation", "correlation_uncertainty", "pair_count", "Station abbreviation", "Scheduled track", "Train name"}
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"data is missing required columns: {missing}")

    filtered = (
        data.filter(pl.col("correlation").is_not_null())
        .filter(pl.col("pair_count") > min_pair_count)
        .sort("correlation", descending=True)
        .with_columns(
            pl.format(
                "{} | {} | {}",
                pl.col("Station abbreviation"),
                pl.col("Scheduled track"),
                pl.col("Train name"),
            ).alias("cause_label"),
        )
    )

    if filtered.is_empty():
        raise ValueError("No rows remain after filtering nulls and applying min_pair_count.")

    labels = filtered.get_column("cause_label").to_list()
    values = filtered.get_column("correlation").to_list()
    uncertainties = filtered.get_column("correlation_uncertainty").to_list()

    x = range(len(labels))

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x, values, yerr=uncertainties, capsize=4)
    ax.set_xlabel("Candidate cause event")
    ax.set_ylabel("Correlation")
    ax.set_title(title)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=75, ha="right")
    ax.grid(axis="y", linestyle="--")
    fig.tight_layout()

    return fig
