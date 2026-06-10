from datetime import time, timedelta

import polars as pl

from rsys_analyser.analysis.causality_investigation import correlation
from rsys_analyser.core import CombinedSelector, LocationSelector, TimeSelector, TrainSelector


def test_correlation_selects_latest_prior_cause_per_effect(exploration_data: pl.DataFrame) -> None:
    result = correlation(
        exploration_data,
        location_cause_hypothesis=LocationSelector(tiploc="AAA"),
        location_effect_hypothesis=LocationSelector(tiploc="BBB"),
    )

    assert result.height == 1
    assert result.get_column("Actual departure_cause").to_list() == [time(8, 36)]
    assert result.get_column("Actual departure_effect").to_list() == [time(11, 6)]


def test_correlation_supports_train_selectors(exploration_data: pl.DataFrame) -> None:
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
