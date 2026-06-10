from datetime import time

import polars as pl
import pytest

from rsys_analyser.core import CombinedSelector, LocationSelector, TimeSelector, TrainSelector, deadlock_selection, extract_pattern


@deadlock_selection
def _simulation_numbers(data: pl.DataFrame) -> list[int]:
    return data.get_column("Simulation no.").to_list()


@extract_pattern
def _pattern_parts(data: pl.DataFrame) -> pl.DataFrame:
    return data.select("Operator Code", "Service Code", "Origin TIPLOC", "Destination TIPLOC")


def test_deadlock_selection_excludes_deadlocks_by_default(core_data: pl.DataFrame) -> None:
    assert _simulation_numbers(core_data) == [1, 3, 4]


def test_deadlock_selection_only_deadlocks(core_data: pl.DataFrame) -> None:
    assert _simulation_numbers(core_data, only_deadlocks=True) == [2]


def test_deadlock_selection_allows_full_dataset(core_data: pl.DataFrame) -> None:
    assert _simulation_numbers(core_data, exclude_deadlocks=False) == [1, 2, 3, 4]


def test_deadlock_selection_rejects_conflicting_flags(core_data: pl.DataFrame) -> None:
    with pytest.raises(ValueError, match="Cannot have exclude_deadlocks and only_deadlocks"):
        _simulation_numbers(core_data, exclude_deadlocks=True, only_deadlocks=True)


def test_extract_pattern_adds_expected_columns(core_data: pl.DataFrame) -> None:
    extracted = _pattern_parts(core_data)

    assert extracted.columns == ["Operator Code", "Service Code", "Origin TIPLOC", "Destination TIPLOC"]
    assert extracted.row(0) == ("WA", "100", "AAA", "BBB")
    assert extracted.row(2) == ("GW", "200", "BBB", "CCC")


def test_extract_pattern_rejects_unknown_pattern_format(core_data: pl.DataFrame) -> None:
    with pytest.raises(NotImplementedError, match="is not implemented"):
        _pattern_parts(core_data, pattern_format="custom-format")


def test_time_selector_handles_regular_and_overnight_intervals(core_data: pl.DataFrame) -> None:
    daytime_selector = TimeSelector(scheduled_arrival_interval=(time(7, 0), time(8, 30)))
    overnight_selector = TimeSelector(scheduled_arrival_interval=(time(23, 0), time(1, 0)))

    daytime = core_data.filter(daytime_selector.get_filter())
    overnight = core_data.filter(overnight_selector.get_filter())

    assert daytime.get_column("Simulation no.").to_list() == [1]
    assert overnight.get_column("Simulation no.").to_list() == [3, 4]


def test_location_selector_filters_with_list_values(core_data: pl.DataFrame) -> None:
    selector = LocationSelector(tiploc=["AAA", "BBB"], line=["L1"])
    result = core_data.filter(selector.get_filter())

    assert result.get_column("Simulation no.").to_list() == [1, 4]


def test_train_selector_filters_multiple_fields(core_data: pl.DataFrame) -> None:
    selector = TrainSelector(operator_code=["WA", "GW"], train_class="C1")
    result = core_data.filter(selector.get_filter())

    assert result.get_column("Simulation no.").to_list() == [1, 3, 4]


def test_combined_selector_and_train_location_and_time_filters(core_data: pl.DataFrame) -> None:
    selector = CombinedSelector(
        train_selector=TrainSelector(headcode="1A04", operator_code="WA"),
        location_selector=LocationSelector(tiploc="AAA", line="L1"),
        time_selector=TimeSelector(scheduled_arrival_interval=(time(23, 0), time(23, 59, 59))),
    )

    result = core_data.filter(selector.get_filter())
    assert result.get_column("Simulation no.").to_list() == [4]


def test_combined_selector_without_any_selector_matches_all_rows(core_data: pl.DataFrame) -> None:
    selector = CombinedSelector()

    result = core_data.filter(selector.get_filter())
    assert result.get_column("Simulation no.").to_list() == [1, 2, 3, 4]


def test_combined_selector_with_location_only_uses_location_filter(core_data: pl.DataFrame) -> None:
    selector = CombinedSelector(location_selector=LocationSelector(tiploc="AAA", line="L1"))

    result = core_data.filter(selector.get_filter())
    assert result.get_column("Simulation no.").to_list() == [1, 4]
