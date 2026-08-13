"""Tests for executing tutorial markdown directly."""

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
import pytest

import rsys_toolbox.io.eval_manager as eval_manager
from rsys_toolbox.scaffold.tutorial_markdown import discover_tutorial_pages, execute_markdown_python, extract_python_blocks

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_extract_python_blocks_finds_tutorial_snippets() -> None:
    """Extract Python blocks from tutorial markdown pages."""
    tutorial_files = discover_tutorial_pages(REPO_ROOT / "mkdocs.yaml")

    assert [file_path.name for file_path in tutorial_files] == [
        "index.md",
        "setup.md",
        "load-data.md",
        "exploration.md",
        "punctuality.md",
        "train-profiles.md",
        "causality.md",
        "flighting.md",
    ]

    block_counts = [len(extract_python_blocks(file_path, show_plots=False)) for file_path in tutorial_files]

    assert block_counts == [0, 0, 2, 4, 4, 6, 2, 0]


@pytest.mark.xfail
def test_tutorial_markdown_runs_end_to_end(
    tutorial_data: pl.DataFrame,
    monkeypatch,  # noqa: ANN001
    tmp_path: Path,
) -> None:
    """Execute tutorial markdown pages and verify the expected artifacts."""
    tutorial_files = discover_tutorial_pages(REPO_ROOT / "mkdocs.yaml")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(eval_manager, "load", lambda _path: tutorial_data)
    monkeypatch.setattr(plt, "show", lambda: None)

    namespace = execute_markdown_python(tutorial_files)

    assert namespace["dls"].get_column("Simulation no.").to_list() == [2]
    assert namespace["stations"].height > 0
    assert namespace["punctuality_data"].height > 0

    csv_path = tmp_path / "punctuality_data_worst_tiploc.csv"
    png_path = tmp_path / f"worst_trains_{namespace['worst_tiploc']}.png"
    lateness_path = tmp_path / f"median_lateness_profile_{namespace['bad_headcode']}.png"
    runtime_path = tmp_path / f"median_runtime_profile_{namespace['bad_headcode']}.png"

    assert csv_path.exists()
    assert csv_path.stat().st_size > 0
    assert png_path.exists()
    assert png_path.stat().st_size > 0
    assert lateness_path.exists()
    assert lateness_path.stat().st_size > 0
    assert runtime_path.exists()
    assert runtime_path.stat().st_size > 0
    lateness_hist_path = tmp_path / "lateness_histogram_BHAMNWS.png"
    dwell_hist_path = tmp_path / "dwell_histogram_BHAMNWS.png"
    assert lateness_hist_path.exists()
    assert lateness_hist_path.stat().st_size > 0
    assert dwell_hist_path.exists()
    assert dwell_hist_path.stat().st_size > 0
