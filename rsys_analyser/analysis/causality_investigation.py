from rsys_analyser.io.data_types import EvalManagerData
from rsys_analyser.core import deadlock_selection, extract_pattern, TimeSelection, LocationSelection, TrainSelection

import polars as pl


@deadlock_selection
@extract_pattern
def correlation(
        data: EvalManagerData,
        location_cause_hypothesis: LocationSelection,
        location_effect_hypothesis: LocationSelection,
        train_cause_hypothesis: TrainSelection,
        train_effect_hypothesis: TrainSelection
    ) -> pl.DataFrame:

    df_effect = data.filter(
        train_effect_hypothesis.get_filter() & location_effect_hypothesis.get_filter()
    )
    return df_effect
