"""Tests for flighting plotting helpers."""

from datetime import time

import polars as pl
import pytest
from matplotlib.patches import Rectangle

from rsys_toolbox.analysis import build_out_of_order_flighting_summary
from rsys_toolbox.plots import plot_out_of_order_flighting


@pytest.fixture
def flighting_data() -> pl.DataFrame:
    """Create data with one stable and one reordered simulation.

    Returns:
        Mock Eval Manager rows for flighting tests.

    """
    return pl.DataFrame({
        "Simulation no.": [1, 1, 1, 1, 2, 2, 2, 2],
        "Station index": [0, 1, 0, 1, 0, 1, 0, 1],
        "Station abbreviation": ["AAA", "BBB", "AAA", "BBB", "AAA", "BBB", "AAA", "BBB"],
        "Station name": ["Alpha", "Beta", "Alpha", "Beta", "Alpha", "Beta", "Alpha", "Beta"],
        "Scheduled track": ["1", "1", "1", "1", "1", "1", "1", "1"],
        "Route": ["R1", "R1", "R1", "R1", "R1", "R1", "R1", "R1"],
        "Train no.": ["T1", "T1", "T2", "T2", "T1", "T1", "T2", "T2"],
        "Train name": ["1A01", "1A01", "2B02", "2B02", "1A01", "1A01", "2B02", "2B02"],
        "Scheduled arrival": [
            time(8, 0),
            time(8, 10),
            time(8, 5),
            time(8, 15),
            time(8, 0),
            time(8, 10),
            time(8, 5),
            time(8, 15),
        ],
        "Actual arrival": [
            time(8, 0),
            time(8, 10),
            time(8, 5),
            time(8, 15),
            time(8, 6),
            time(8, 16),
            time(8, 1),
            time(8, 11),
        ],
        "SchedDep": [
            time(8, 1),
            time(8, 11),
            time(8, 6),
            time(8, 16),
            time(8, 1),
            time(8, 11),
            time(8, 6),
            time(8, 16),
        ],
        "Actual departure": [
            time(8, 1),
            time(8, 11),
            time(8, 6),
            time(8, 16),
            time(8, 7),
            time(8, 17),
            time(8, 2),
            time(8, 12),
        ],
    })


def test_build_out_of_order_flighting_summary_ranks_stations(flighting_data: pl.DataFrame) -> None:
    """Verify station summary reports reordered simulations in descending order."""
    summary = build_out_of_order_flighting_summary(flighting_data, mode="station", event="departure", include_track=True)

    assert summary.to_dicts() == [
        {
            "resource_label": "AAA (Alpha) / 1",
            "simulation_count": 2,
            "out_of_order_simulation_count": 1,
            "out_of_order_simulation_proportion": 0.5,
        },
        {
            "resource_label": "BBB (Beta) / 1",
            "simulation_count": 2,
            "out_of_order_simulation_count": 1,
            "out_of_order_simulation_proportion": 0.5,
        },
    ]


def test_build_out_of_order_flighting_summary_ranks_sections(flighting_data: pl.DataFrame) -> None:
    """Verify section summary compares train order over consecutive station pairs."""
    summary = build_out_of_order_flighting_summary(flighting_data, mode="section", event="departure")

    assert summary.to_dicts() == [
        {
            "resource_label": "AAA → BBB",
            "simulation_count": 2,
            "out_of_order_simulation_count": 1,
            "out_of_order_simulation_proportion": 0.5,
        }
    ]


def test_plot_out_of_order_flighting_uses_summary_values(flighting_data: pl.DataFrame) -> None:
    """Verify plotted bars use out-of-order simulation percentages."""
    fig = plot_out_of_order_flighting(flighting_data, mode="section", event="departure")
    axes = fig.axes[0]
    first_bar = axes.patches[0]

    assert [tick.get_text() for tick in axes.get_yticklabels()] == ["AAA → BBB"]
    assert isinstance(first_bar, Rectangle)
    assert first_bar.get_width() == pytest.approx(50.0)
