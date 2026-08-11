"""Verify that the eval_managers load function works."""

from pathlib import Path

import polars as pl
import pytest

from rsys_toolbox.io.eval_manager import _extract_pattern_columns, load


@pytest.mark.parametrize(
    ("pattern", "expected_operator", "expected_service", "expected_origin", "expected_destination"),
    [
        # Format 1: /Operator/ServiceCode/Origin/Destination  (four slash-separated segments)
        ("/EX/21381901/OOCINT/SHENFLD", "EX", "21381901", "OOCINT", "SHENFLD"),
        # Format 2: /Operator/ServiceCode/Origin-Destination  (dash-joined origin/dest)
        ("/WA/52407530/SOTD107-KNGSBCE", "WA", "52407530", "SOTD107", "KNGSBCE"),
    ],
)
def test_extract_pattern_columns(
    pattern: str,
    expected_operator: str | None,
    expected_service: str | None,
    expected_origin: str | None,
    expected_destination: str | None,
) -> None:
    """Verify that all recognised pattern formats are parsed correctly."""
    df = _extract_pattern_columns(pl.DataFrame({"Pattern": [pattern]}))

    assert df["Operator Code"][0] == expected_operator
    assert df["Service Code"][0] == expected_service
    assert df["Origin TIPLOC"][0] == expected_origin
    assert df["Destination TIPLOC"][0] == expected_destination


def test_extract_pattern_columns_raises_on_unrecognised_pattern() -> None:
    """Verify that an unrecognised Pattern value raises a ValueError."""
    with pytest.raises(ValueError, match="Unrecognised Pattern values"):
        _extract_pattern_columns(pl.DataFrame({"Pattern": ["UNKNOWN"]}))


def test_load_reads_eval_manager_asset_from_assets(eval_manager_asset_path: Path) -> None:
    """Verify that the load function leads to a DataFrame as expected."""
    df_from_path = load(eval_manager_asset_path)
    df_from_str = load(str(eval_manager_asset_path))

    assert df_from_path.height > 0
    assert isinstance(df_from_path, pl.DataFrame)
    assert df_from_path.shape == df_from_str.shape


def test_load_casts_expected_columns_to_final_types(loaded_eval_manager: pl.DataFrame) -> None:
    """Verify that the load function does the correct casts."""
    schema = loaded_eval_manager.schema

    assert schema["Simulation no."] == pl.Int32
    assert schema["Deadlock"] == pl.Boolean
    assert schema["Replatforming"] == pl.Boolean
    assert schema["Change of direction of travel"] == pl.Boolean


def test_load_filters_non_simulation_summary_rows(loaded_eval_manager: pl.DataFrame) -> None:
    """Verify that the load function removes the summary columns."""
    simulation_values = loaded_eval_manager.get_column("Simulation no.")
    min_simulation = simulation_values.min()

    assert simulation_values.null_count() == 0
    assert isinstance(min_simulation, int)
    assert min_simulation >= 0
