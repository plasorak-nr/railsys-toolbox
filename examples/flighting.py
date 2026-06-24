"""An example of plotting out-of-order train flighting."""

from pathlib import Path

import polars as pl

from rsys_toolbox.analysis import build_out_of_order_flighting_summary
from rsys_toolbox.core import LocationSelector
from rsys_toolbox.io.eval_manager import load
from rsys_toolbox.plots import plot_out_of_order_flighting

DATA_PATH = Path("assets/MRH S1 Eval Manager 2105.csv")
TIPLOC = "BGRN"
TOP_N = 15

data = load(DATA_PATH)

location_selector = LocationSelector(tiploc=TIPLOC)
station_data = data.filter(location_selector.get_filter())
if station_data.is_empty():
    print(f"No rows found for {TIPLOC}; using all stations instead.")
    station_data = data
    location_selector = None

station_summary = build_out_of_order_flighting_summary(
    station_data,
    mode="station",
    event="departure",
    include_track=True,
    max_items=TOP_N,
)

print(f"Most out-of-order station flighting for {TIPLOC}:")
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
    event="departure",
    include_track=True,
    max_items=TOP_N,
    location_selector=location_selector,
)
station_output_path = "flighting_out_of_order_stations.png"
station_fig.savefig(station_output_path, dpi=150, bbox_inches="tight")
print(f"Saved station flighting plot to {station_output_path}")

section_summary = build_out_of_order_flighting_summary(
    data,
    mode="section",
    event="departure",
    max_items=TOP_N,
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
    max_items=TOP_N,
)
section_output_path = "flighting_out_of_order_sections.png"
section_fig.savefig(section_output_path, dpi=150, bbox_inches="tight")
print(f"Saved section flighting plot to {section_output_path}")
