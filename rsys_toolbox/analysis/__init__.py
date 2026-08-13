"""Analysis helpers for exploring and correlating Eval Manager data."""

from rsys_toolbox.analysis.causality_investigation import correlation, correlation_search
from rsys_toolbox.analysis.exploration import (
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
from rsys_toolbox.analysis.flighting import build_out_of_order_flighting_summary
from rsys_toolbox.analysis.punctuality import calculate_punctuality
from rsys_toolbox.core import filter_zzztiplocs

__all__ = [
    "build_out_of_order_flighting_summary",
    "calculate_punctuality",
    "correlation",
    "correlation_search",
    "dump_train",
    "filter_zzztiplocs",
    "get_all_lines_at_station",
    "get_all_operator_codes",
    "get_all_patterns",
    "get_all_service_codes",
    "get_all_stations",
    "get_all_train_categories",
    "get_all_train_classes",
    "get_all_train_formations",
    "get_all_train_names",
    "get_all_train_numbers",
    "get_valid_simulations",
    "search_events",
]
