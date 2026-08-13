"""Core selectors and decorators for filtering evaluation-manager data."""

import operator
from dataclasses import dataclass
from datetime import time
from functools import reduce
from logging import getLogger

import polars as pl

logger = getLogger("core")


def _fmt_str(v: str | list[str]) -> str:
    return "[" + ", ".join(v) + "]" if isinstance(v, list) else v


TimeInterval = tuple[time, time]
TimeIntervals = TimeInterval | list[TimeInterval]


def require_columns(data: pl.DataFrame, required_columns: set[str]) -> None:
    """Raise when a dataframe is missing required columns.

    Args:
        data: Dataframe to validate.
        required_columns: Column names that must be present.

    Raises:
        ValueError: If any required column is absent.

    """
    missing = sorted(required_columns.difference(data.columns))
    if missing:
        raise ValueError(f"data is missing required columns: {missing}")


def filter_zzztiplocs(data: pl.DataFrame) -> pl.DataFrame:
    """Return data without synthetic ``ZZZ`` TIPLOC rows.

    Args:
        data: Dataframe to filter.

    Returns:
        DataFrame with rows where ``Station abbreviation`` starts with ``ZZZ`` removed.

    """
    if "Station abbreviation" not in data.columns:
        return data

    return data.filter(~pl.col("Station abbreviation").str.starts_with("ZZZ"))


def filter_deadlocks(
    data: pl.DataFrame,
    *,
    exclude_deadlocks: bool | None = None,
    only_deadlocks: bool | None = None,
) -> pl.DataFrame:
    """Filter an Eval Manager dataframe by deadlock simulation membership.

    By default (both flags ``None``) deadlock simulations are excluded.
    Pass ``exclude_deadlocks=False`` and ``only_deadlocks=False`` explicitly
    to receive the full unfiltered dataset.

    Args:
        data: Source Eval Manager dataframe.
        exclude_deadlocks: When ``True``, remove all simulations that contain
            at least one deadlock row. Mutually exclusive with
            ``only_deadlocks``. Defaults to ``True`` when both flags are
            ``None``.
        only_deadlocks: When ``True``, keep only simulations that contain at
            least one deadlock row. Mutually exclusive with
            ``exclude_deadlocks``.

    Returns:
        A filtered view of ``data`` according to the requested deadlock
        selection mode.

    Raises:
        ValueError: If both ``exclude_deadlocks`` and ``only_deadlocks`` are
            ``True``.

    """
    if exclude_deadlocks and only_deadlocks:
        msg = "Cannot have exclude_deadlocks and only_deadlocks valid at the same time"
        raise ValueError(msg)

    if exclude_deadlocks is None and only_deadlocks is None:
        exclude_deadlocks = True

    deadlock_sims = data.filter(pl.col("Deadlock")).get_column("Simulation no.").unique()

    if exclude_deadlocks:
        return data.filter(~pl.col("Simulation no.").is_in(deadlock_sims.implode()))

    if only_deadlocks:
        return data.filter(pl.col("Simulation no.").is_in(deadlock_sims.implode()))

    return data


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

    def __repr__(self) -> str:  # noqa: D105
        def _fmt(interval: TimeInterval) -> str:
            return f"[{interval[0]} → {interval[1]}]"

        def _fmt_intervals(intervals: TimeIntervals) -> str:
            if isinstance(intervals, list):
                return "[" + ", ".join(_fmt(i) for i in intervals) + "]"
            return _fmt(intervals)

        parts = []
        if self.scheduled_arrival_interval is not None:
            parts.append(f"scheduled_arrival_interval={_fmt_intervals(self.scheduled_arrival_interval)}")
        if self.actual_arrival_interval is not None:
            parts.append(f"actual_arrival_interval={_fmt_intervals(self.actual_arrival_interval)}")
        if self.scheduled_departure_interval is not None:
            parts.append(f"scheduled_departure_interval={_fmt_intervals(self.scheduled_departure_interval)}")
        if self.actual_departure_interval is not None:
            parts.append(f"actual_departure_interval={_fmt_intervals(self.actual_departure_interval)}")
        return f"TimeSelector({', '.join(parts)})"

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

    def __repr__(self) -> str:  # noqa: D105
        parts = []
        if self.tiploc is not None:
            parts.append(f"tiploc={_fmt_str(self.tiploc)}")
        if self.track is not None:
            parts.append(f"track={_fmt_str(self.track)}")
        if self.route is not None:
            parts.append(f"route={_fmt_str(self.route)}")
        if self.line is not None:
            parts.append(f"line={_fmt_str(self.line)}")
        return f"LocationSelector({', '.join(parts)})"

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

    def __repr__(self) -> str:  # noqa: D105
        parts = []
        if self.headcode is not None:
            parts.append(f"headcode={_fmt_str(self.headcode)}")
        if self.operator_code is not None:
            parts.append(f"operator_code={_fmt_str(self.operator_code)}")
        if self.service_code is not None:
            parts.append(f"service_code={_fmt_str(self.service_code)}")
        if self.pattern is not None:
            parts.append(f"pattern={_fmt_str(self.pattern)}")
        if self.train_number is not None:
            parts.append(f"train_number={_fmt_str(self.train_number)}")
        if self.train_class is not None:
            parts.append(f"train_class={_fmt_str(self.train_class)}")
        if self.train_formation is not None:
            parts.append(f"train_formation={_fmt_str(self.train_formation)}")
        return f"TrainSelector({', '.join(parts)})"

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

    def __repr__(self) -> str:  # noqa: D105
        parts = []
        if self.train_selector is not None:
            parts.append(f"train_selector={self.train_selector!r}")
        if self.location_selector is not None:
            parts.append(f"location_selector={self.location_selector!r}")
        if self.time_selector is not None:
            parts.append(f"time_selector={self.time_selector!r}")
        return f"CombinedSelector({', '.join(parts)})"

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


Selector = CombinedSelector | LocationSelector | TimeSelector | TrainSelector


def apply_selector_filter(
    data: pl.DataFrame,
    *,
    combined_selector: CombinedSelector | None = None,
    location_selector: LocationSelector | None = None,
    time_selector: TimeSelector | None = None,
    train_selector: TrainSelector | None = None,
) -> pl.DataFrame:
    """Apply selector and optional expression filtering to an Eval Manager dataframe.

    Each provided selector's ``get_filter()`` expression is collected and
    combined with logical AND. The result is applied to ``data`` via
    ``data.filter()``. If no selectors are provided the data is returned
    unmodified.

    Args:
        data: Source Eval Manager dataframe.
        combined_selector: Optional combined train/location/time selector.
        location_selector: Optional location selector.
        time_selector: Optional time selector.
        train_selector: Optional train selector.

    Returns:
        The filtered dataframe.

    """
    filters = []
    for selector in (combined_selector, location_selector, time_selector, train_selector):
        if selector is not None:
            filters.append(selector.get_filter())

    if not filters:
        filters = [pl.lit(True)]

    selector_expr = reduce(operator.and_, filters)

    return data.filter(selector_expr)
