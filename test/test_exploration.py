from datetime import time

import polars as pl
import pytest

from rsys_analyser.analysis.exploration import (
    get_all_lines_at_station,
    get_all_operator_codes,
    get_all_patterns,
    get_all_service_codes,
    get_all_stations,
    get_all_train_categories,
    get_all_train_classes,
    get_all_train_formations,
    get_all_train_names,
    get_all_train_numbers,
    get_valid_simulations,
    search_events,
)
from rsys_analyser.core import CombinedSelector, LocationSelector, TimeSelector, TrainSelector


def test_search_events_without_filters_excludes_deadlock_simulations(exploration_data: pl.DataFrame) -> None:
    result = search_events(exploration_data)

    assert result.height == 4
    assert result.get_column("Simulation no.").to_list() == [1, 1, 3, 3]


def test_search_events_applies_combined_selectors(exploration_data: pl.DataFrame) -> None:
    selector = CombinedSelector(
        train_selector=TrainSelector(operator_code="WA", service_code="100"),
        location_selector=LocationSelector(tiploc="AAA", line="L1"),
        time_selector=TimeSelector(scheduled_arrival_interval=(time(7, 0), time(9, 0))),
    )

    result = search_events(exploration_data, selector=selector)

    assert result.height == 2
    assert result.get_column("Train no.").to_list() == ["T1", "T1"]


def test_get_valid_simulations_returns_unique_sorted_without_deadlocks(exploration_data: pl.DataFrame) -> None:
    result = get_valid_simulations(exploration_data)
    assert result.to_dicts() == [{"Simulation no.": 1}, {"Simulation no.": 3}]


def test_get_all_stations_returns_unique_sorted_without_deadlocks(exploration_data: pl.DataFrame) -> None:
    result = get_all_stations(exploration_data)
    assert result.to_dicts() == [
        {"Station abbreviation": "AAA", "Station name": "Alpha"},
        {"Station abbreviation": "BBB", "Station name": "Beta"},
    ]


def test_get_all_lines_at_station_excludes_deadlocks_and_returns_unique_sorted_rows(exploration_data: pl.DataFrame) -> None:
    result = get_all_lines_at_station(exploration_data, "AAA")

    assert result.columns == [
        "Station abbreviation",
        "Station name",
        "Line abbr.",
        "Route",
        "Scheduled track",
    ]
    assert result.to_dicts() == [
        {
            "Station abbreviation": "AAA",
            "Station name": "Alpha",
            "Line abbr.": "L1",
            "Route": "R1",
            "Scheduled track": "1",
        },
        {
            "Station abbreviation": "AAA",
            "Station name": "Alpha",
            "Line abbr.": "L2",
            "Route": "R2",
            "Scheduled track": "2",
        },
    ]


@pytest.mark.parametrize(
    ("func", "column_name", "expected"),
    [
        (get_all_operator_codes, "Operator Code", ["GW", "WA"]),
        (get_all_service_codes, "Service Code", ["100", "200"]),
        (get_all_patterns, "Pattern", ["/GW/200/AAA-CCC", "/WA/100/AAA-BBB", "/WA/100/BBB-AAA"]),
        (get_all_train_numbers, "Train no.", ["T1", "T2", "T3"]),
        (get_all_train_names, "Train name", ["1A01", "1A03", "2B02"]),
        (get_all_train_classes, "Train class", ["C1", "C2"]),
        (get_all_train_categories, "Train category", [1, 2]),
        (get_all_train_formations, "Train formation ID", ["F1", "F2", "F3"]),
    ],
)
def test_pattern_and_train_getters_return_unique_sorted_values_without_deadlocks(
    exploration_data: pl.DataFrame,
    func,
    column_name: str,
    expected: list[str] | list[int],
) -> None:
    result = func(exploration_data)
    assert result.get_column(column_name).to_list() == expected
