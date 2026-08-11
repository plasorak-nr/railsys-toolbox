"""Pytest fixtures definitions."""

from datetime import time
from pathlib import Path

import matplotlib
import polars as pl
import pytest

from rsys_toolbox.io.eval_manager import load

matplotlib.use("Agg")

ASSET_CANDIDATES = [
    "MRH S1 Eval Manager 2105.csv",
]


@pytest.fixture(scope="session")
def eval_manager_asset_path() -> Path:
    """Get the path for the eval manager.

    Returns:
        The path to the first matching Eval Manager asset file.

    Raises:
        FileNotFoundError: If no configured asset candidate exists.

    """
    assets_dir = Path(__file__).resolve().parents[1] / "assets"
    for file_name in ASSET_CANDIDATES:
        candidate = assets_dir / file_name
        if candidate.exists():
            return candidate

    expected = ", ".join(ASSET_CANDIDATES)
    raise FileNotFoundError(f"Could not find any expected Eval Manager asset in {assets_dir}: {expected}")


@pytest.fixture(scope="session")
def loaded_eval_manager(eval_manager_asset_path: Path) -> pl.DataFrame:
    """Get the data for the eval manager.

    Args:
        eval_manager_asset_path: Fixture-provided path to the source CSV.

    Returns:
        The loaded Eval Manager dataframe fixture.

    """
    return load(eval_manager_asset_path)


@pytest.fixture
def exploration_data() -> pl.DataFrame:
    """Get mock Eval Manager data for exploratory analysis tests.

    Returns:
        A dataframe with representative exploration test rows.

    """
    return pl.DataFrame(
        {
            "Simulation no.": [1, 1, 2, 3, 3],
            "Deadlock": [False, False, True, False, False],
            "Station index": [0, 1, 0, 0, 2],
            "Station abbreviation": ["AAA", "AAA", "AAA", "BBB", "AAA"],
            "Station name": ["Alpha", "Alpha", "Alpha", "Beta", "Alpha"],
            "Line abbr.": ["L1", "L2", "LX", "LB", "L1"],
            "Route": ["R1", "R2", "RX", "RB", "R1"],
            "Scheduled track": ["1", "2", "9", "1", "1"],
            "Pattern": [
                "/WA/100/AAA-BBB",
                "/GW/200/AAA-CCC",
                "/DL/300/AAA-DDD",
                "/WA/100/BBB-AAA",
                "/WA/100/AAA-BBB",
            ],
            "Operator Code": ["WA", "GW", "DL", "WA", "WA"],
            "Service Code": ["100", "200", "300", "100", "100"],
            "Origin TIPLOC": ["AAA", "AAA", "AAA", "BBB", "AAA"],
            "Destination TIPLOC": ["BBB", "CCC", "DDD", "AAA", "BBB"],
            "Train no.": ["T1", "T2", "TD", "T3", "T1"],
            "Train name": ["1A01", "2B02", "9D99", "1A03", "1A01"],
            "Train class": ["C1", "C2", "CD", "C1", "C1"],
            "Train category": [1, 2, 9, 1, 1],
            "Train formation ID": ["F1", "F2", "FD", "F3", "F1"],
            "Arrival lateness": [60, 120, 180, 240, 60],
            "Scheduled arrival": [time(8, 0), time(9, 0), time(10, 0), time(11, 0), time(8, 30)],
            "Actual arrival": [time(8, 1), time(9, 2), time(10, 3), time(11, 4), time(8, 31)],
            "SchedDep": [time(8, 5), time(9, 5), time(10, 5), time(11, 5), time(8, 35)],
            "Actual departure": [time(8, 6), time(9, 6), time(10, 6), time(11, 6), time(8, 36)],
        },
    )


@pytest.fixture
def core_data() -> pl.DataFrame:
    """Get mock data for core selector and decorator tests.

    Returns:
        A dataframe with representative core test rows.

    """
    return pl.DataFrame(
        {
            "Simulation no.": [1, 2, 3, 4],
            "Deadlock": [False, True, False, False],
            "Pattern": [
                "/WA/100/AAA-BBB",
                "/DL/999/AAA-XXX",
                "/GW/200/BBB-CCC",
                "/WA/100/AAA-BBB",
            ],
            "Station abbreviation": ["AAA", "AAA", "BBB", "AAA"],
            "Scheduled track": ["1", "2", "1", "1"],
            "Route": ["R1", "R9", "R2", "R1"],
            "Line abbr.": ["L1", "L9", "L2", "L1"],
            "Train name": ["1A01", "9D99", "2B02", "1A04"],
            "Operator Code": ["WA", "DL", "GW", "WA"],
            "Service Code": ["100", "999", "200", "100"],
            "Origin TIPLOC": ["AAA", "AAA", "BBB", "AAA"],
            "Destination TIPLOC": ["BBB", "XXX", "CCC", "BBB"],
            "Train no.": ["T1", "TD", "T2", "T4"],
            "Train class": ["C1", "CD", "C1", "C1"],
            "Train formation ID": ["F1", "FD", "F2", "F4"],
            "Scheduled arrival": [time(8, 0), time(9, 0), time(0, 30), time(23, 30)],
            "Actual arrival": [time(8, 1), time(9, 1), time(0, 31), time(23, 31)],
            "SchedDep": [time(8, 5), time(9, 5), time(0, 35), time(23, 35)],
            "Actual departure": [time(8, 6), time(9, 6), time(0, 36), time(23, 36)],
        },
    )


@pytest.fixture
def dump_train_data() -> pl.DataFrame:
    """Get mock Eval Manager data for dump_train tests.

    Returns:
        A dataframe with representative dump_train test rows.

    """
    return pl.DataFrame(
        {
            "Simulation no.": [1, 1, 1, 1, 1, 2, 2, 2],
            "Deadlock": [False, False, False, False, False, True, True, True],
            "Station index": [0, 1, 2, 3, 4, 0, 1, 2],
            "Station abbreviation": ["AAA", "CCC", "BBB", "DDD", "EEE", "AAA", "BBB", "CCC"],
            "Station name": ["Alpha", "Charlie", "Beta", "Delta", "Echo", "Alpha", "Beta", "Charlie"],
            "Route": ["R1", "R1", "R1", "R1", "R1", "R2", "R2", "R2"],
            "Train no.": ["T1", "T1", "T1", "T1", "T1", "TD", "TD", "TD"],
            "Train name": ["1A01", "1A01", "1A01", "1A01", "1A01", "9D99", "9D99", "9D99"],
            "Scheduled arrival": [time(8, 0), time(8, 10), time(8, 20), time(8, 30), time(8, 40), time(9, 0), time(9, 10), time(9, 20)],
            "Actual arrival": [time(8, 1), time(8, 11), time(8, 21), time(8, 31), time(8, 41), time(9, 1), time(9, 11), time(9, 21)],
            "SchedDep": [time(8, 5), time(8, 15), time(8, 25), time(8, 35), time(8, 45), time(9, 5), time(9, 15), time(9, 25)],
            "Actual departure": [time(8, 6), time(8, 16), time(8, 26), time(8, 36), time(8, 46), time(9, 6), time(9, 16), time(9, 26)],
        },
    )
