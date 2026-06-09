from rsys_analyser.analysis.causality_investigation import correlation, TrainSelector, CombinedSelector, TimeSelector, LocationSelector
from rsys_analyser.io.eval_manager import load

trains_effect = TrainSelector(operator_code=["HF", "WA"])
trains_cause = TrainSelector(operator_code=["HF", "DB"])
location_effect = LocationSelector(tiploc=["CBOMJN", "PRYBRNJ", "SOHOSJ", "BRDSLYL", "BSCTULP"])
location_cause = LocationSelector(tiploc=["FOUROKS", "PRYBRNJ", "SOHOSJ"])

data = load("assets/MRH S1 Eval Manager 2105.csv")

print(
    "correlation",
    correlation(
        data,
        location_cause_hypothesis=location_cause,
        location_effect_hypothesis=location_effect,
        train_cause_hypothesis=trains_cause,
        train_effect_hypothesis=trains_effect,
    )
    .select("Pattern", "Station name", "Train name", "Actual departure")
    .unique(),
)
