import operator
from dataclasses import dataclass
from datetime import time
from functools import reduce, wraps
from logging import getLogger

import polars as pl

from rsys_analyser.io.eval_manager import EvalManagerData

logger = getLogger("core")

TimeInterval = tuple[time, time]
TimeIntervals = TimeInterval | list[TimeInterval]


def deadlock_selection(function):
    @wraps(function)
    def wrap(data: EvalManagerData, *args, exclude_deadlocks: bool | None = None, only_deadlocks: bool | None = None, **kwargs):
        if exclude_deadlocks and only_deadlocks:
            msg = "Cannot have exclude_deadlocks and only_deadlocks valid at the same time"
            raise ValueError(msg)

        if exclude_deadlocks is None and only_deadlocks is None:
            exclude_deadlocks = True

        deadlock_sims = data.filter(pl.col("Deadlock")).get_column("Simulation no.").unique()

        if exclude_deadlocks:
            return function(data.filter(~pl.col("Simulation no.").is_in(deadlock_sims.implode())), *args, **kwargs)

        if only_deadlocks:
            return function(data.filter(pl.col("Simulation no.").is_in(deadlock_sims.implode())), *args, **kwargs)

        return function(data, *args, **kwargs)

    return wrap


def extract_pattern(function):
    @wraps(function)
    def wrap(data: EvalManagerData, *args, pattern_format: str = "operator_code/service_code/origin-destination", **kwargs):
        if pattern_format == "operator_code/service_code/origin-destination":
            #'/WA/52407530/SOTD107-KNGSBCE'
            pattern_re = r"^/([^/]+)/([^/]+)/([^-/]+)-([^-/]+)$"
            df = data.with_columns(
                pl.col("Pattern").str.extract(pattern_re, group_index=1).alias("Operator Code"),
                pl.col("Pattern").str.extract(pattern_re, group_index=2).alias("Service Code"),
                pl.col("Pattern").str.extract(pattern_re, group_index=3).alias("Origin TIPLOC"),
                pl.col("Pattern").str.extract(pattern_re, group_index=4).alias("Destination TIPLOC"),
            )
        else:
            msg = f"Pattern {pattern_format!r} is not implemented"
            raise NotImplementedError(msg)

        return function(df, *args, **kwargs)

    return wrap


@dataclass
class TimeSelector:
    scheduled_arrival_interval: TimeIntervals | None = None
    actual_arrival_interval: TimeIntervals | None = None
    scheduled_departure_interval: TimeIntervals | None = None
    actual_departure_interval: TimeIntervals | None = None

    @staticmethod
    def _interval_expr(col_name: str, interval: TimeInterval) -> pl.Expr:
        start, end = interval
        col = pl.col(col_name)

        # Handle overnight windows, e.g. 23:00 -> 01:00.
        if start <= end:
            return col.is_between(start, end, closed="both")

        return col.is_between(start, time(23, 59, 59, 999999), closed="both") | col.is_between(time(0, 0), end, closed="both")

    @classmethod
    def _intervals_expr(cls, col_name: str, intervals: TimeIntervals) -> pl.Expr:
        normalized = intervals if isinstance(intervals, list) else [intervals]
        interval_filters = [cls._interval_expr(col_name, interval) for interval in normalized]
        return reduce(operator.or_, interval_filters)

    def get_filter(self) -> pl.Expr:
        time_filter = []

        if self.scheduled_arrival_interval is not None:
            time_filter += [self._intervals_expr("Scheduled arrival", self.scheduled_arrival_interval)]

        if self.actual_arrival_interval is not None:
            time_filter += [self._intervals_expr("Actual arrival", self.actual_arrival_interval)]

        if self.scheduled_departure_interval is not None:
            time_filter += [self._intervals_expr("SchedDep", self.scheduled_departure_interval)]

        if self.actual_departure_interval is not None:
            time_filter += [self._intervals_expr("Actual departure", self.actual_departure_interval)]

        if not time_filter:
            return pl.lit(True)

        return reduce(operator.and_, time_filter)


@dataclass
class LocationSelector:
    tiploc: str | list[str] | None = None
    track: str | list[str] | None = None
    route: str | list[str] | None = None
    line: str | list[str] | None = None

    @staticmethod
    def _expr(col_name: str, value: str | list[str]) -> pl.Expr:
        if isinstance(value, list):
            return pl.col(col_name).is_in(value)
        return pl.col(col_name) == value

    def get_filter(self) -> pl.Expr:
        location_filter = []

        if self.tiploc:
            location_filter += [self._expr("Station abbreviation", self.tiploc)]

        if self.track:
            location_filter += [self._expr("Scheduled track", self.track)]

        if self.route:
            location_filter += [self._expr("Route", self.route)]

        if self.line:
            location_filter += [self._expr("Line abbr.", self.line)]

        if not location_filter:
            return pl.lit(True)

        return reduce(operator.and_, location_filter)


@dataclass
class TrainSelector:
    headcode: str | list[str] | None = None
    operator_code: str | list[str] | None = None
    service_code: str | list[str] | None = None
    pattern: str | list[str] | None = None
    train_number: str | list[str] | None = None
    train_class: str | list[str] | None = None
    train_formation: str | list[str] | None = None

    @staticmethod
    def _expr(col_name: str, value: str | list[str]) -> pl.Expr:
        if isinstance(value, list):
            return pl.col(col_name).is_in(value)
        return pl.col(col_name) == value

    def get_filter(self) -> pl.Expr:
        effect_filter = []

        if self.headcode:
            effect_filter += [self._expr("Train name", self.headcode)]

        if self.operator_code:
            effect_filter += [self._expr("Operator Code", self.operator_code)]

        if self.service_code:
            effect_filter += [self._expr("Service Code", self.service_code)]

        if self.pattern:
            effect_filter += [self._expr("Pattern", self.pattern)]

        if self.train_number:
            effect_filter += [self._expr("Train no.", self.train_number)]

        if self.train_class:
            effect_filter += [self._expr("Train class", self.train_class)]

        if self.train_formation:
            effect_filter += [self._expr("Train formation ID", self.train_formation)]

        if not effect_filter:
            return pl.lit(True)

        return reduce(operator.and_, effect_filter)


@dataclass
class CombinedSelector:
    train_selector: TrainSelector | None = None
    location_selector: LocationSelector | None = None
    time_selector: TimeSelector | None = None

    def get_filter(self) -> pl.Expr:
        filters = []

        if self.train_selector is not None:
            filters.append(self.train_selector.get_filter())

        if self.location_selector is not None:
            filters.append(self.location_selector.get_filter())

        if self.time_selector is not None:
            filters.append(self.time_selector.get_filter())

        if not filters:
            return pl.lit(True)

        return reduce(operator.and_, filters)
