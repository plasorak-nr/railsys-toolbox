from rsys_analyser.analysis.causality_investigation import LocationSelector, TrainSelector
from rsys_analyser.io.eval_manager import load

trains_effect = TrainSelector(operator_code=["HF", "WA"])
trains_cause = TrainSelector(operator_code=["HF", "DB"])
location_effect = LocationSelector(tiploc=["CBOMJN", "PRYBRNJ", "SOHOSJ", "BRDSLYL", "BSCTULP"])
location_cause = LocationSelector(tiploc=["FOUROKS", "PRYBRNJ", "SOHOSJ"])

data = load("assets/MRH S1 Eval Manager 2105.csv")

