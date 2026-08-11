"""Aggregate punctuality plotting utilities."""

from datetime import timedelta

import matplotlib.pyplot as plt
import polars as pl
from matplotlib.figure import Figure

from rsys_toolbox.core import require_columns


def _format_tolerance(tolerance: timedelta) -> str:
    """Return a compact human-readable label for a punctuality tolerance.

    Returns:
        A string such as ``"T-4m30s"`` or ``"T-5min"``.

    """
    total_seconds = int(tolerance.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    if seconds == 0:
        return f"T-{minutes}min"
    return f"T-{minutes}m{seconds:02d}s"


def plot_train_punctuality(
    data: pl.DataFrame,
    location_name: str | None = None,
    tiploc: str | None = None,
    tolerance: timedelta | None = None,
) -> Figure:
    """Plot a horizontal bar chart of train punctuality with uncertainty bars.

    The input data is expected to come from
    plotted as-is — sort it and filter to the desired number
    of trains before calling this function.

    Args:
        data: Punctuality dataframe as returned by
            :func:`rsys_toolbox.analysis.punctuality`, grouped by
            ``["Train name", "Operator Code"]`` and pre-sorted.
        location_name: Human-readable station name for the chart title.
        tiploc: Station TIPLOC code for the chart title.
        tolerance: Punctuality tolerance used when computing the data, shown
            in the chart title.

    Returns:
        A matplotlib Figure containing the horizontal bar chart.

    Raises:
        ValueError: If required columns are missing or the dataframe is empty.

    """
    require_columns(
        data,
        {"Train name", "Operator Code", "punctuality", "punctuality_uncertainty"},
    )

    if data.is_empty():
        raise ValueError("data is empty")

    labels = [
        f"{train} ({operator})"
        for train, operator in zip(
            data.get_column("Train name").to_list(),
            data.get_column("Operator Code").to_list(),
            strict=True,
        )
    ]
    values = [v * 100 for v in data.get_column("punctuality").to_list()]
    uncertainties = [v * 100 for v in data.get_column("punctuality_uncertainty").to_list()]
    y_pos = list(range(len(labels)))

    fig_height = max(4.0, len(labels) * 0.4)
    fig, ax = plt.subplots(figsize=(10, fig_height))

    ax.barh(y_pos, values, xerr=uncertainties, capsize=4)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Punctuality (%)")
    ax.set_xlim(0, 105)
    ax.grid(axis="x", alpha=0.3)
    ax.invert_yaxis()

    title_parts: list[str] = [f"{len(labels)} trains"]
    if location_name and tiploc:
        title_parts.append(f"at {location_name} ({tiploc})")
    elif tiploc:
        title_parts.append(f"at {tiploc}")
    elif location_name:
        title_parts.append(f"at {location_name}")
    if tolerance is not None:
        title_parts.append(f"({_format_tolerance(tolerance)} adherence)")
    ax.set_title(" ".join(title_parts))

    fig.tight_layout()
    return fig
