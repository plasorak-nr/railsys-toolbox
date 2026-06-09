from rsys_analyser.io.data_types import EvalManagerData
from dataclasses import dataclass
import polars as pl

@dataclass
class LocationSelection:
    tiploc: str
    platform: str
    line: str

@dataclass
class TrainSelection:
    headcode: str
    operator: str


def correlation(
        data: EvalManagerData,
        location_cause_hypothesis: LocationSelection,
        location_effect_hypothesis: LocationSelection,
        train_cause_hypothesis: TrainSelection,
        train_effect_hypothesis: TrainSelection
    ) -> pl.DataFrame:

    data.


