from datetime import time
from pathlib import Path

import polars as pl
import pytest

from rsys_analyser.io.eval_manager import load


ASSET_CANDIDATES = [
    "MRH S1 Eval Manager 2105.csv",
]


@pytest.fixture(scope="session")
def eval_manager_asset_path() -> Path:
    assets_dir = Path(__file__).resolve().parents[1] / "assets"
    for file_name in ASSET_CANDIDATES:
        candidate = assets_dir / file_name
        if candidate.exists():
            return candidate

    expected = ", ".join(ASSET_CANDIDATES)
    raise FileNotFoundError(f"Could not find any expected Eval Manager asset in {assets_dir}: {expected}")


@pytest.fixture(scope="session")
def loaded_eval_manager(eval_manager_asset_path: Path) -> pl.DataFrame:
    return load(eval_manager_asset_path)


@pytest.fixture()
def exploration_data() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "Simulation no.": [1, 1, 2, 3, 3],
            "Deadlock": [False, False, True, False, False],
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
            "Train no.": ["T1", "T2", "TD", "T3", "T1"],
            "Train name": ["1A01", "2B02", "9D99", "1A03", "1A01"],
            "Train class": ["C1", "C2", "CD", "C1", "C1"],
            "Train category": [1, 2, 9, 1, 1],
            "Train formation ID": ["F1", "F2", "FD", "F3", "F1"],
            "Scheduled arrival": [time(8, 0), time(9, 0), time(10, 0), time(11, 0), time(8, 30)],
            "Actual arrival": [time(8, 1), time(9, 2), time(10, 3), time(11, 4), time(8, 31)],
            "SchedDep": [time(8, 5), time(9, 5), time(10, 5), time(11, 5), time(8, 35)],
            "Actual departure": [time(8, 6), time(9, 6), time(10, 6), time(11, 6), time(8, 36)],
        }
    )


@pytest.fixture()
def core_data() -> pl.DataFrame:
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
            "Train no.": ["T1", "TD", "T2", "T4"],
            "Train class": ["C1", "CD", "C1", "C1"],
            "Train formation ID": ["F1", "FD", "F2", "F4"],
            "Scheduled arrival": [time(8, 0), time(9, 0), time(0, 30), time(23, 30)],
            "Actual arrival": [time(8, 1), time(9, 1), time(0, 31), time(23, 31)],
            "SchedDep": [time(8, 5), time(9, 5), time(0, 35), time(23, 35)],
            "Actual departure": [time(8, 6), time(9, 6), time(0, 36), time(23, 36)],
        }
    )
