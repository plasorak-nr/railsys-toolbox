"""Verify that the eval_managers load function works."""

from pathlib import Path

import polars as pl

from rsys_toolbox.io.eval_manager import load


def test_load_reads_eval_manager_asset_from_assets(eval_manager_asset_path: Path) -> None:
    """Verify that the load function leads to a DataFrame as expected."""
    asset_path = eval_manager_asset_path

    # Ensure both string and Path inputs are accepted.
    df_from_path = load(asset_path)
    df_from_str = load(str(asset_path))

    assert df_from_path.height > 0
    assert df_from_path.width == 52
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
