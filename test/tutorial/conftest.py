"""Fixtures for tutorial markdown tests."""

from datetime import time

import polars as pl
import pytest


@pytest.fixture
def tutorial_data() -> pl.DataFrame:
    """Get mock Eval Manager data for end-to-end tutorial execution.

    Extends the base exploration data with Birmingham New Street (BHAMNWS)
    rows in dedicated simulations so histogram functions have a single
    identifiable station to operate on.

    Returns:
        A dataframe covering all stations exercised by the tutorial pages.

    """
    return pl.DataFrame(
        {
            "Simulation no.": [1, 1, 2, 3, 3, 4, 5],
            "Deadlock": [False, False, True, False, False, False, False],
            "Station index": [0, 1, 0, 0, 2, 0, 0],
            "Station abbreviation": ["AAA", "AAA", "AAA", "BBB", "AAA", "BHAMNWS", "BHAMNWS"],
            "Station name": ["Alpha", "Alpha", "Alpha", "Beta", "Alpha", "Birmingham New Street", "Birmingham New Street"],
            "Line abbr.": ["L1", "L2", "LX", "LB", "L1", "L1", "L1"],
            "Route": ["R1", "R2", "RX", "RB", "R1", "R1", "R1"],
            "Scheduled track": ["1", "2", "9", "1", "1", "3", "3"],
            "Pattern": [
                "/WA/100/AAA-BBB",
                "/GW/200/AAA-CCC",
                "/DL/300/AAA-DDD",
                "/WA/100/BBB-AAA",
                "/WA/100/AAA-BBB",
                "/WA/100/AAA-BBB",
                "/WA/100/AAA-BBB",
            ],
            "Operator Code": ["WA", "GW", "DL", "WA", "WA", "WA", "WA"],
            "Train no.": ["T1", "T2", "TD", "T3", "T1", "T3", "T3"],
            "Train name": ["1A01", "2B02", "9D99", "1A03", "1A01", "1A03", "1A03"],
            "Train class": ["C1", "C2", "CD", "C1", "C1", "C1", "C1"],
            "Train category": [1, 2, 9, 1, 1, 1, 1],
            "Train formation ID": ["F1", "F2", "FD", "F3", "F1", "F1", "F1"],
            "Arrival lateness": [60, 120, 180, 240, 60, 300, 300],
            "Scheduled arrival": [
                time(8, 0), time(9, 0), time(10, 0), time(11, 0), time(8, 30),
                time(7, 45), time(7, 50),
            ],
            "Actual arrival": [
                time(8, 1), time(9, 2), time(10, 3), time(11, 4), time(8, 31),
                time(7, 50), time(7, 55),
            ],
            "SchedDep": [
                time(8, 5), time(9, 5), time(10, 5), time(11, 5), time(8, 35),
                time(7, 47), time(7, 54),
            ],
            "Actual departure": [
                time(8, 6), time(9, 6), time(10, 6), time(11, 6), time(8, 36),
                time(7, 48), time(7, 55),
            ],
        },
    )
