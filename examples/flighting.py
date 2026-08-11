"""An example of plotting out-of-order train flighting."""

from pathlib import Path

import polars as pl

from rsys_toolbox.analysis import build_out_of_order_flighting_summary
from rsys_toolbox.io.eval_manager import load
from rsys_toolbox.plots import plot_out_of_order_flighting

DATA_PATH = Path("assets/20260512-MIAOpt-SimData_FullMIA.csv")

data = load(DATA_PATH)

station_summary = build_out_of_order_flighting_summary(
    data,
    mode="station",
)

print("Most out-of-order station flighting:")
print(
    station_summary.select(
        "resource_label",
        "simulation_count",
        "out_of_order_simulation_count",
        (pl.col("out_of_order_simulation_proportion") * 100).round(1).alias("out_of_order_percent"),
    )
)


station_fig = plot_out_of_order_flighting(
    data,
    mode="station",
)
station_output_path = "flighting_out_of_order_stations.png"
station_fig.savefig(station_output_path, dpi=150, bbox_inches="tight")
print(f"Saved station flighting plot to {station_output_path}")

section_summary = build_out_of_order_flighting_summary(
    data,
    mode="section",
    event="departure",
)

print("Most out-of-order section flighting:")
print(
    section_summary.select(
        "resource_label",
        "simulation_count",
        "out_of_order_simulation_count",
        (pl.col("out_of_order_simulation_proportion") * 100).round(1).alias("out_of_order_percent"),
    )
)

section_fig = plot_out_of_order_flighting(
    data,
    mode="section",
    event="departure",
)
section_output_path = "flighting_out_of_order_sections.png"
section_fig.savefig(section_output_path, dpi=150, bbox_inches="tight")
print(f"Saved section flighting plot to {section_output_path}")
