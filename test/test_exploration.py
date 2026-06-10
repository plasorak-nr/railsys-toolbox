"""Unit tests for the exploration functions."""

from datetime import time
from typing import Callable

import polars as pl
import pytest

from rsys_analyser.analysis.exploration import (
    dump_train,
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
    """Verify that search_events works."""
    result = search_events(exploration_data)

    assert result.height == 4
    assert result.get_column("Simulation no.").to_list() == [1, 1, 3, 3]


def test_search_events_applies_combined_selectors(exploration_data: pl.DataFrame) -> None:
    """Verify that search_events works with a selector."""
    selector = CombinedSelector(
        train_selector=TrainSelector(operator_code="WA", service_code="100"),
        location_selector=LocationSelector(tiploc="AAA", line="L1"),
        time_selector=TimeSelector(scheduled_arrival_interval=(time(7, 0), time(9, 0))),
    )

    result = search_events(exploration_data, selector=selector)

    assert result.height == 2
    assert result.get_column("Train no.").to_list() == ["T1", "T1"]


def test_get_valid_simulations_returns_unique_sorted_without_deadlocks(exploration_data: pl.DataFrame) -> None:
    """Verify that get_valid_simulations works."""
    result = get_valid_simulations(exploration_data)
    assert result.to_dicts() == [{"Simulation no.": 1}, {"Simulation no.": 3}]


def test_get_all_stations_returns_unique_sorted_without_deadlcks(exploration_data: pl.DataFrame) -> None:
    """Verify that get_all_stations works."""
    result = get_all_stations(exploration_data)
    assert result.to_dicts() == [
        {"Station abbreviation": "AAA", "Station name": "Alpha"},
        {"Station abbreviation": "BBB", "Station name": "Beta"},
    ]


def test_get_all_lines_at_station_excludes_deadlocks_and_returns_unique_sorted_rows(exploration_data: pl.DataFrame) -> None:
    """Verify that get_all_line_at_station works."""
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
    func: Callable[[pl.DataFrame], pl.DataFrame],
    column_name: str,
    expected: list[str] | list[int],
) -> None:
    """Verify that the rest of the exploration functions all work."""
    result = func(exploration_data)
    assert result.get_column(column_name).to_list() == expected


def test_dump_train_returns_all_stops_for_train_sorted_by_station_index(dump_train_data: pl.DataFrame) -> None:
    """Verify that dump_train returns all stops for a train sorted by station index."""
    result = dump_train(dump_train_data, simulation=1, train_filter=TrainSelector(train_number="T1"))

    assert result.height == 5
    assert result.get_column("Station index").to_list() == [0, 1, 2, 3, 4]


def test_dump_train_returns_correct_columns(dump_train_data: pl.DataFrame) -> None:
    """Verify that dump_train returns the expected columns."""
    result = dump_train(dump_train_data, simulation=1, train_filter=TrainSelector(train_number="T1"))

    assert result.columns == [
        "Station index",
        "Station abbreviation",
        "Station name",
        "Route",
        "Scheduled arrival",
        "Actual arrival",
        "SchedDep",
        "Actual departure",
    ]


def test_dump_train_returns_correct_station_sequence(dump_train_data: pl.DataFrame) -> None:
    """Verify that dump_train returns the correct station sequence."""
    result = dump_train(dump_train_data, simulation=1, train_filter=TrainSelector(train_number="T1"))

    stations = result.get_column("Station abbreviation").to_list()
    assert stations == ["AAA", "CCC", "BBB", "DDD", "EEE"]


def test_dump_train_returns_correct_times(dump_train_data: pl.DataFrame) -> None:
    """Verify that dump_train returns correct scheduled and actual times."""
    result = dump_train(dump_train_data, simulation=1, train_filter=TrainSelector(train_number="T1"))

    # Check first stop
    first_row = result.row(0, named=True)
    assert first_row["Scheduled arrival"] == time(8, 0)
    assert first_row["Actual arrival"] == time(8, 1)
    assert first_row["SchedDep"] == time(8, 5)
    assert first_row["Actual departure"] == time(8, 6)

    # Check last stop
    last_row = result.row(4, named=True)
    assert last_row["Scheduled arrival"] == time(8, 40)
    assert last_row["Actual arrival"] == time(8, 41)
    assert last_row["SchedDep"] == time(8, 45)
    assert last_row["Actual departure"] == time(8, 46)


def test_dump_train_raises_error_when_no_train_matches(dump_train_data: pl.DataFrame) -> None:
    """Verify that dump_train raises ValueError when no train matches the filter."""
    with pytest.raises(ValueError, match="No train found matching filter"):
        dump_train(dump_train_data, simulation=1, train_filter=TrainSelector(train_number="NONEXISTENT"))


def test_dump_train_raises_error_when_multiple_trains_match(dump_train_data: pl.DataFrame) -> None:
    """Verify that dump_train raises ValueError when multiple trains match the filter."""
    # Add a test that would match multiple trains - in this case simulation 1 only has T1,
    # so we need to create a scenario where multiple trains match
    # Let's test with an empty filter on a simulation that has multiple stops from same train
    # Actually, our fixture only has one train per simulation, so we can't test this scenario easily
    # Instead, let's skip this test or modify the fixture to have multiple trains
    # For now, let's create a custom dataframe for this test
    multi_train_data = pl.DataFrame(
        {
            "Simulation no.": [1, 1, 1, 1],
            "Deadlock": [False, False, False, False],
            "Station index": [0, 1, 0, 1],
            "Station abbreviation": ["AAA", "BBB", "AAA", "BBB"],
            "Station name": ["Alpha", "Beta", "Alpha", "Beta"],
            "Route": ["R1", "R1", "R2", "R2"],
            "Train no.": ["T1", "T1", "T2", "T2"],
            "Train name": ["1A01", "1A01", "1A02", "1A02"],
            "Scheduled arrival": [time(8, 0), time(8, 10), time(9, 0), time(9, 10)],
            "Actual arrival": [time(8, 1), time(8, 11), time(9, 1), time(9, 11)],
            "SchedDep": [time(8, 5), time(8, 15), time(9, 5), time(9, 15)],
            "Actual departure": [time(8, 6), time(8, 16), time(9, 6), time(9, 16)],
        },
    )

    with pytest.raises(ValueError, match="Multiple trains matched filter"):
        # Empty filter matches all trains in the simulation
        dump_train(multi_train_data, simulation=1, train_filter=TrainSelector())


def test_dump_train_excludes_deadlock_simulations(dump_train_data: pl.DataFrame) -> None:
    """Verify that dump_train excludes deadlock simulations by default."""
    # Simulation 2 only has deadlock trains
    with pytest.raises(ValueError, match="No train found matching filter"):
        dump_train(dump_train_data, simulation=2, train_filter=TrainSelector(train_number="TD"))


def test_dump_train_filters_by_simulation(dump_train_data: pl.DataFrame) -> None:
    """Verify that dump_train correctly filters by simulation number."""
    result = dump_train(dump_train_data, simulation=1, train_filter=TrainSelector(train_number="T1"))

    # Verify the result has data and is for the correct simulation
    assert result.height == 5


def test_dump_train_works_with_train_name_selector(dump_train_data: pl.DataFrame) -> None:
    """Verify that dump_train works with train name selector."""
    result = dump_train(dump_train_data, simulation=1, train_filter=TrainSelector(headcode="1A01"))

    assert result.height == 5
