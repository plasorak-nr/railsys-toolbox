"""Flighting plotting utilities for train ordering across simulations."""

import matplotlib.pyplot as plt
import polars as pl
from matplotlib.figure import Figure

from rsys_toolbox.analysis.flighting import FlightingEvent, FlightingMode, build_out_of_order_flighting_summary
from rsys_toolbox.core import remove_zzztiplocs, selector_filter


@remove_zzztiplocs
@selector_filter()
def plot_out_of_order_flighting(
    data: pl.DataFrame,
    mode: FlightingMode = "station",
    event: FlightingEvent = "departure",
    include_track: bool = False,
    max_items: int | None = 20,
) -> Figure:
    """Plot stations or sections by descending out-of-order simulation rate.

    A station/section is counted as out-of-order in a simulation when at least
    two trains are present and their scheduled event order differs from their
    actual event order.

    Args:
        data: Input dataframe (full dataset or pre-filtered subset).
        mode: Whether to compare order at each station or over each section.
        event: Timestamp pair used for scheduled-versus-actual ordering.
        include_track: Whether station labels should include scheduled track.
        max_items: Optional number of highest-rate resources to plot.

    Returns:
        A matplotlib Figure containing a horizontal bar chart.

    Raises:
        ValueError: If filtering leaves no rows or no comparable resources.

    """
    if data.is_empty():
        raise ValueError("No rows matched the provided selectors")

    summary = build_out_of_order_flighting_summary(
        data,
        mode=mode,
        event=event,
        include_track=include_track,
        max_items=max_items,
        remove_zzztiplocs=False,
    )

    labels = summary.get_column("resource_label").to_list()
    proportions = summary.get_column("out_of_order_simulation_proportion").to_list()
    out_of_order_counts = summary.get_column("out_of_order_simulation_count").to_list()
    simulation_counts = summary.get_column("simulation_count").to_list()

    fig_height = max(4.0, len(labels) * 0.4)
    fig, axes = plt.subplots(figsize=(10, fig_height))
    y_positions = list(range(len(labels)))

    axes.barh(y_positions, [proportion * 100.0 for proportion in proportions], color="tab:blue", alpha=0.8)
    axes.set_yticks(y_positions)
    axes.set_yticklabels(labels)
    axes.invert_yaxis()
    axes.set_xlim(0.0, 100.0)
    axes.set_xlabel("Simulations with at least one out of order train (%)")
    axes.set_ylabel("Station" if mode == "station" else "Section")
    axes.set_title("Out of order Train")
    axes.grid(True, axis="x", linestyle="--", alpha=0.4)

    for y_position, proportion, out_of_order_count, simulation_count in zip(y_positions, proportions, out_of_order_counts, simulation_counts, strict=True):
        axes.text(
            min((proportion * 100.0) + 1.0, 99.0),
            y_position,
            f"{proportion:.0%} ({out_of_order_count}/{simulation_count})",
            va="center",
            fontsize=9,
        )

    fig.tight_layout()

    return fig
