"""Verify that the causality works."""

from datetime import time, timedelta

import polars as pl

from rsys_analyser.analysis.causality_investigation import correlation, correlation_search
from rsys_analyser.core import CombinedSelector, LocationSelector, TimeSelector, TrainSelector


def test_correlation_selects_latest_prior_cause_per_effect(exploration_data: pl.DataFrame) -> None:
    """Verify that causality works when using LocationSelectors."""
    result = correlation(
        exploration_data,
        location_cause_hypothesis=LocationSelector(tiploc="AAA"),
        location_effect_hypothesis=LocationSelector(tiploc="BBB"),
    )

    assert result.height == 1
    assert result.get_column("Actual departure_cause").to_list() == [time(8, 36)]
    assert result.get_column("Actual departure_effect").to_list() == [time(11, 6)]


def test_correlation_supports_train_selectors(exploration_data: pl.DataFrame) -> None:
    """Verify that causality works when using TrainSelectors."""
    result = correlation(
        exploration_data,
        train_cause_hypothesis=TrainSelector(operator_code="WA", train_number="T1"),
        train_effect_hypothesis=TrainSelector(train_number="T3"),
    )

    assert result.height == 1
    assert result.get_column("Simulation no._effect").to_list() == [3]
    assert result.get_column("Train no._cause").to_list() == ["T1"]
    assert result.get_column("Train no._effect").to_list() == ["T3"]


def test_correlation_supports_time_selectors(exploration_data: pl.DataFrame) -> None:
    """Verify that causality works when using TimeSelector."""
    result = correlation(
        exploration_data,
        location_cause_hypothesis=LocationSelector(tiploc="AAA"),
        location_effect_hypothesis=LocationSelector(tiploc="BBB"),
        time_cause_hypothesis=TimeSelector(actual_departure_interval=(time(8, 0), time(9, 0))),
        time_effect_hypothesis=TimeSelector(actual_departure_interval=(time(11, 0), time(11, 10))),
    )

    assert result.height == 1
    assert result.get_column("Actual departure_cause").to_list() == [time(8, 36)]
    assert result.get_column("Actual departure_effect").to_list() == [time(11, 6)]


def test_correlation_supports_combined_selectors(exploration_data: pl.DataFrame) -> None:
    """Verify that causality works when using CombinedSelector."""
    cause_selector = CombinedSelector(
        location_selector=LocationSelector(tiploc="AAA"),
        train_selector=TrainSelector(operator_code="WA"),
        time_selector=TimeSelector(actual_departure_interval=(time(8, 0), time(9, 0))),
    )
    effect_selector = CombinedSelector(
        location_selector=LocationSelector(tiploc="BBB"),
        train_selector=TrainSelector(train_number="T3"),
    )

    result = correlation(
        exploration_data,
        combined_cause_hypothesis=cause_selector,
        combined_effect_hypothesis=effect_selector,
    )

    assert result.height == 1
    assert result.get_column("Train no._cause").to_list() == ["T1"]
    assert result.get_column("Train no._effect").to_list() == ["T3"]


def test_correlation_applies_max_cause_window(exploration_data: pl.DataFrame) -> None:
    """Verify that causality works correctly with max_cause_window."""
    narrow_window_result = correlation(
        exploration_data,
        location_cause_hypothesis=LocationSelector(tiploc="AAA"),
        location_effect_hypothesis=LocationSelector(tiploc="BBB"),
        max_cause_window=timedelta(hours=1),
    )
    wide_window_result = correlation(
        exploration_data,
        location_cause_hypothesis=LocationSelector(tiploc="AAA"),
        location_effect_hypothesis=LocationSelector(tiploc="BBB"),
        max_cause_window=timedelta(hours=3),
    )

    assert narrow_window_result.height == 0
    assert wide_window_result.height == 1
    assert wide_window_result.get_column("Actual departure_cause").to_list() == [time(8, 36)]
    assert wide_window_result.get_column("Actual departure_effect").to_list() == [time(11, 6)]


def test_correlation_search_scores_all_past_window_candidates() -> None:
    """Verify correlation_search evaluates all eligible past events."""
    data = pl.DataFrame(
        {
            "Simulation no.": [1, 1, 1, 2, 2, 2],
            "Deadlock": [False, False, False, False, False, False],
            "Station abbreviation": ["AAA", "CCC", "BBB", "AAA", "CCC", "BBB"],
            "Station name": ["Alpha", "Charlie", "Beta", "Alpha", "Charlie", "Beta"],
            "Line abbr.": ["L1", "L2", "LB", "L1", "L2", "LB"],
            "Route": ["R1", "R2", "RB", "R1", "R2", "RB"],
            "Scheduled track": ["1", "2", "1", "1", "2", "1"],
            "Pattern": [
                "/WA/100/AAA-BBB",
                "/GW/200/CCC-BBB",
                "/WA/100/BBB-AAA",
                "/WA/100/AAA-BBB",
                "/GW/200/CCC-BBB",
                "/WA/100/BBB-AAA",
            ],
            "Train no.": ["T1", "T2", "TE", "T1", "T2", "TE"],
            "Train name": ["1A01", "2B02", "1E00", "1A01", "2B02", "1E00"],
            "Train class": ["C1", "C2", "C1", "C1", "C2", "C1"],
            "Train category": [1, 2, 1, 1, 2, 1],
            "Train formation ID": ["F1", "F2", "FE", "F1", "F2", "FE"],
            "Scheduled arrival": [
                time(8, 0),
                time(8, 30),
                time(9, 55),
                time(8, 5),
                time(8, 35),
                time(10, 0),
            ],
            "Actual arrival": [
                time(8, 2),
                time(8, 33),
                time(10, 0),
                time(8, 6),
                time(8, 36),
                time(10, 3),
            ],
            "SchedDep": [
                time(8, 10),
                time(8, 40),
                time(10, 0),
                time(8, 15),
                time(8, 45),
                time(10, 5),
            ],
            "Actual departure": [
                time(8, 20),
                time(8, 50),
                time(10, 10),
                time(8, 35),
                time(8, 50),
                time(10, 15),
            ],
        },
    )

    result = correlation_search(
        data,
        location_effect_hypothesis=LocationSelector(tiploc="BBB"),
        max_cause_window=timedelta(hours=2),
    )

    assert result.height == 2
    assert sorted(result.get_column("Station abbreviation").to_list()) == ["AAA", "CCC"]
    assert result.get_column("pair_count").to_list() == [2, 2]
    assert result.get_column("simulation_count").to_list() == [2, 2]
    assert all(value is not None for value in result.get_column("correlation").to_list())
