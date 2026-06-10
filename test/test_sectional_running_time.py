"""Tests for train graph plotting helpers."""

from datetime import time

import polars as pl
import pytest

from rsys_analyser.plots.punctuality_train import plot_median_lateness_profile
from rsys_analyser.plots.sectional_running_time import plot_median_runtime_profile


def test_plot_median_runtime_profile_computes_scheduled_and_median_actual_minutes() -> None:
    """Verify the runtime profile values use scheduled and median actual segment times."""
    train_log = pl.DataFrame({
        "Simulation no.": [1, 1, 1, 2, 2, 2],
        "Station index": [0, 1, 2, 0, 1, 2],
        "Station abbreviation": ["AAA", "BBB", "CCC", "AAA", "BBB", "CCC"],
        "Station name": ["Alpha", "Beta", "Charlie", "Alpha", "Beta", "Charlie"],
        "Scheduled arrival": [
            time(8, 0),
            time(8, 10),
            time(8, 20),
            time(8, 0),
            time(8, 10),
            time(8, 20),
        ],
        "Actual arrival": [
            time(8, 1),
            time(8, 11),
            time(8, 21),
            time(8, 2),
            time(8, 14),
            time(8, 26),
        ],
        "SchedDep": [
            time(8, 2),
            time(8, 12),
            time(8, 22),
            time(8, 2),
            time(8, 12),
            time(8, 22),
        ],
        "Actual departure": [
            time(8, 3),
            time(8, 13),
            time(8, 23),
            time(8, 4),
            time(8, 16),
            time(8, 28),
        ],
        "Train name": ["1A01", "1A01", "1A01", "1A01", "1A01", "1A01"],
        "Operator Code": ["WA", "WA", "WA", "WA", "WA", "WA"],
    })

    fig = plot_median_runtime_profile(train_log)
    ax = fig.axes[0]

    assert [tick.get_text() for tick in ax.get_xticklabels()] == [
        "AAA dwell",
        "AAA → BBB",
        "BBB dwell",
        "BBB → CCC",
        "CCC dwell",
    ]

    assert ax.lines[0].get_ydata() == pytest.approx([2.0, 9.0, 2.0, 9.0, 2.0])
    assert ax.lines[1].get_ydata() == pytest.approx([2.0, 8.0, 2.0, 8.0, 2.0])
    assert len(ax.collections) == 1


def test_plot_median_runtime_profile_drops_short_dwells() -> None:
    """Verify dwells shorter than 10 seconds are not plotted."""
    train_log = pl.DataFrame({
        "Simulation no.": [1, 1, 1, 2, 2, 2],
        "Station index": [0, 1, 2, 0, 1, 2],
        "Station abbreviation": ["AAA", "BBB", "CCC", "AAA", "BBB", "CCC"],
        "Station name": ["Alpha", "Beta", "Charlie", "Alpha", "Beta", "Charlie"],
        "Scheduled arrival": [
            time(8, 0, 0),
            time(8, 10, 0),
            time(8, 20, 0),
            time(8, 0, 0),
            time(8, 10, 0),
            time(8, 20, 0),
        ],
        "Actual arrival": [
            time(8, 0, 1),
            time(8, 10, 5),
            time(8, 20, 1),
            time(8, 0, 2),
            time(8, 10, 6),
            time(8, 20, 2),
        ],
        "SchedDep": [
            time(8, 0, 5),
            time(8, 12, 0),
            time(8, 22, 0),
            time(8, 0, 5),
            time(8, 12, 0),
            time(8, 22, 0),
        ],
        "Actual departure": [
            time(8, 0, 6),
            time(8, 12, 5),
            time(8, 22, 1),
            time(8, 0, 7),
            time(8, 12, 6),
            time(8, 22, 2),
        ],
    })

    fig = plot_median_runtime_profile(train_log)
    ax = fig.axes[0]

    assert [tick.get_text() for tick in ax.get_xticklabels()] == [
        "AAA → BBB",
        "BBB dwell",
        "BBB → CCC",
        "CCC dwell",
    ]


def test_plot_median_runtime_profile_requires_expected_columns() -> None:
    """Verify missing required columns raise a ValueError."""
    with pytest.raises(ValueError, match="missing required columns"):
        plot_median_runtime_profile(
            pl.DataFrame({
                "Station index": [0],
                "Scheduled arrival": [time(8, 0)],
                "Actual arrival": [time(8, 1)],
                "SchedDep": [time(8, 5)],
            })
        )


def test_plot_median_runtime_profile_skips_missing_actual_times() -> None:
    """Verify missing actual timestamps do not crash plotting."""
    train_log = pl.DataFrame({
        "Simulation no.": [1, 1, 1, 2, 2, 2],
        "Station index": [0, 1, 2, 0, 1, 2],
        "Station abbreviation": ["AAA", "BBB", "CCC", "AAA", "BBB", "CCC"],
        "Station name": ["Alpha", "Beta", "Charlie", "Alpha", "Beta", "Charlie"],
        "Scheduled arrival": [time(8, 0), time(8, 10), time(8, 20), time(8, 0), time(8, 10), time(8, 20)],
        "Actual arrival": [time(8, 1), None, time(8, 21), time(8, 2), time(8, 14), time(8, 26)],
        "SchedDep": [time(8, 2), time(8, 12), time(8, 22), time(8, 2), time(8, 12), time(8, 22)],
        "Actual departure": [time(8, 3), None, time(8, 23), time(8, 4), time(8, 16), time(8, 28)],
    })

    fig = plot_median_runtime_profile(train_log)
    ax = fig.axes[0]

    assert [tick.get_text() for tick in ax.get_xticklabels()] == [
        "AAA dwell",
        "AAA → BBB",
        "BBB dwell",
        "BBB → CCC",
        "CCC dwell",
    ]


def test_plot_median_lateness_profile_computes_median_and_envelope() -> None:
    """Verify the lateness profile uses median and includes IQR envelope."""
    train_log = pl.DataFrame({
        "Simulation no.": [1, 1, 1, 2, 2, 2],
        "Station index": [0, 1, 2, 0, 1, 2],
        "Station abbreviation": ["AAA", "BBB", "CCC", "AAA", "BBB", "CCC"],
        "Station name": ["Alpha", "Beta", "Charlie", "Alpha", "Beta", "Charlie"],
        "Scheduled arrival": [
            time(8, 0),
            time(8, 10),
            time(8, 20),
            time(8, 0),
            time(8, 10),
            time(8, 20),
        ],
        "Actual arrival": [
            time(8, 1),
            time(8, 11),
            time(8, 21),
            time(8, 2),
            time(8, 14),
            time(8, 26),
        ],
        "SchedDep": [
            time(8, 2),
            time(8, 12),
            time(8, 22),
            time(8, 2),
            time(8, 12),
            time(8, 22),
        ],
        "Actual departure": [
            time(8, 3),
            time(8, 13),
            time(8, 23),
            time(8, 4),
            time(8, 16),
            time(8, 28),
        ],
    })

    fig = plot_median_lateness_profile(train_log)
    ax = fig.axes[0]

    assert ax.lines[0].get_ydata() == pytest.approx([0.0, 1.0, 0.0, 1.0, 0.0])
    assert len(ax.collections) == 1


def test_plot_median_lateness_profile_drops_short_dwells() -> None:
    """Verify lateness profile applies the same short-dwell filtering."""
    train_log = pl.DataFrame({
        "Simulation no.": [1, 1, 1, 2, 2, 2],
        "Station index": [0, 1, 2, 0, 1, 2],
        "Station abbreviation": ["AAA", "BBB", "CCC", "AAA", "BBB", "CCC"],
        "Station name": ["Alpha", "Beta", "Charlie", "Alpha", "Beta", "Charlie"],
        "Scheduled arrival": [
            time(8, 0, 0),
            time(8, 10, 0),
            time(8, 20, 0),
            time(8, 0, 0),
            time(8, 10, 0),
            time(8, 20, 0),
        ],
        "Actual arrival": [
            time(8, 0, 1),
            time(8, 10, 5),
            time(8, 20, 1),
            time(8, 0, 2),
            time(8, 10, 6),
            time(8, 20, 2),
        ],
        "SchedDep": [
            time(8, 0, 5),
            time(8, 12, 0),
            time(8, 22, 0),
            time(8, 0, 5),
            time(8, 12, 0),
            time(8, 22, 0),
        ],
        "Actual departure": [
            time(8, 0, 6),
            time(8, 12, 5),
            time(8, 22, 1),
            time(8, 0, 7),
            time(8, 12, 6),
            time(8, 22, 2),
        ],
    })

    fig = plot_median_lateness_profile(train_log)
    ax = fig.axes[0]

    assert [tick.get_text() for tick in ax.get_xticklabels()] == [
        "AAA → BBB",
        "BBB dwell",
        "BBB → CCC",
        "CCC dwell",
    ]
