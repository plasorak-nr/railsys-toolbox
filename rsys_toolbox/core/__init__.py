"""Core selectors and decorators for filtering evaluation-manager data."""

import operator
from dataclasses import dataclass
from datetime import time
from functools import reduce, wraps
from logging import getLogger
from typing import Callable, TypeVar

import polars as pl

from rsys_toolbox.io.eval_manager import EvalManagerData

logger = getLogger("core")

TimeInterval = tuple[time, time]
TimeIntervals = TimeInterval | list[TimeInterval]
T = TypeVar("T")

def remove_zzztiplocs(function: Callable[..., T]) -> Callable[..., T]:
    """Wrap a query function so onl the real TIPLOCs are considered.

    Args:
        function: Query function that accepts a dataframe as first argument.

    Returns:
        A wrapped function with ``remove_zzztiplocs`` filtering behaviour
    """
    @wraps(function)
    def wrap(
        data: EvalManagerData,
        *args: object,
        remove_zzztiplocs: bool = True,
        **kwargs: object,
    ):
        if remove_zzztiplocs:
            return function(
                data.filter(
                    ~pl.col('Station abbreviation').str.starts_with('ZZZ')
                ),
                *args,
                **kwargs
            )
        return function(data, *args, **kwargs)

    return wrap


def deadlock_selection(function: Callable[..., T]) -> Callable[..., T]:
    """Wrap a query function so it can exclude or isolate deadlock simulations.

    Args:
        function: Query function that accepts a dataframe as first argument.

    Returns:
        A wrapped function with ``exclude_deadlocks`` and ``only_deadlocks``
        filtering behaviour.

    """

    @wraps(function)
    def wrap(
        data: EvalManagerData,
        *args: object,
        exclude_deadlocks: bool | None = None,
        only_deadlocks: bool | None = None,
        **kwargs: object,
    ) -> T:
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


def extract_pattern(function: Callable[..., T]) -> Callable[..., T]:
    """Wrap a query function so pattern values are expanded into columns.

    Args:
        function: Query function that expects extracted pattern columns.

    Returns:
        A wrapped function that enriches the dataframe with extracted pattern
        parts before delegating to ``function``.

    """

    @wraps(function)
    def wrap(
        data: EvalManagerData,
        *args: object,
        pattern_format: str = "operator_code/service_code/origin-destination",
        **kwargs: object,
    ) -> T:
        if pattern_format == "operator_code/service_code/origin-destination":
            # '/WA/52407530/SOTD107-KNGSBCE'
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
    """Build a Polars expression for filtering rows by time windows."""

    scheduled_arrival_interval: TimeIntervals | None = None
    actual_arrival_interval: TimeIntervals | None = None
    scheduled_departure_interval: TimeIntervals | None = None
    actual_departure_interval: TimeIntervals | None = None

    @staticmethod
    def _interval_expr(col_name: str, interval: TimeInterval) -> pl.Expr:
        """Build an expression for a single time interval, including overnight windows.

        Args:
            col_name: Name of the time column to filter.
            interval: Inclusive start/end time tuple.

        Returns:
            A Polars expression that matches values inside the interval.

        """
        start, end = interval
        col = pl.col(col_name)

        # Handle overnight windows, e.g. 23:00 -> 01:00.
        if start <= end:
            return col.is_between(start, end, closed="both")

        return col.is_between(start, time(23, 59, 59, 999999), closed="both") | col.is_between(time(0, 0), end, closed="both")

    @classmethod
    def _intervals_expr(cls, col_name: str, intervals: TimeIntervals) -> pl.Expr:
        """Combine one or more intervals for the same column into a single expression.

        Args:
            col_name: Name of the time column to filter.
            intervals: One interval or a list of intervals.

        Returns:
            A Polars expression that matches any of the configured intervals.

        """
        normalized = intervals if isinstance(intervals, list) else [intervals]
        interval_filters = [cls._interval_expr(col_name, interval) for interval in normalized]
        return reduce(operator.or_, interval_filters)

    def get_filter(self) -> pl.Expr:
        """Return the combined time filter expression for all configured intervals.

        Returns:
            A Polars expression for filtering rows by time fields.

        """
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
    """Build a Polars expression for filtering rows by location fields."""

    tiploc: str | list[str] | None = None
    track: str | list[str] | None = None
    route: str | list[str] | None = None
    line: str | list[str] | None = None

    @staticmethod
    def _expr(col_name: str, value: str | list[str]) -> pl.Expr:
        """Build an equality or membership expression for a location field.

        Args:
            col_name: Name of the location column to filter.
            value: Single accepted value or list of accepted values.

        Returns:
            A Polars expression for an exact or set-based location match.

        """
        if isinstance(value, list):
            return pl.col(col_name).is_in(value)
        return pl.col(col_name) == value

    def get_filter(self) -> pl.Expr:
        """Return the combined location filter expression for all configured fields.

        Returns:
            A Polars expression for filtering rows by location fields.

        """
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
    """Build a Polars expression for filtering rows by train metadata."""

    headcode: str | list[str] | None = None
    operator_code: str | list[str] | None = None
    service_code: str | list[str] | None = None
    pattern: str | list[str] | None = None
    train_number: str | list[str] | None = None
    train_class: str | list[str] | None = None
    train_formation: str | list[str] | None = None

    @staticmethod
    def _expr(col_name: str, value: str | list[str]) -> pl.Expr:
        """Build an equality or membership expression for a train field.

        Args:
            col_name: Name of the train column to filter.
            value: Single accepted value or list of accepted values.

        Returns:
            A Polars expression for an exact or set-based train match.

        """
        if isinstance(value, list):
            return pl.col(col_name).is_in(value)
        return pl.col(col_name) == value

    def get_filter(self) -> pl.Expr:
        """Return the combined train filter expression for all configured fields.

        Returns:
            A Polars expression for filtering rows by train fields.

        """
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
    """Combine train, location, and time selectors into a single filter."""

    train_selector: TrainSelector | None = None
    location_selector: LocationSelector | None = None
    time_selector: TimeSelector | None = None

    def get_filter(self) -> pl.Expr:
        """Return the combined filter expression for any configured sub-selectors.

        Returns:
            A Polars expression combining train, location, and time filters.

        """
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
