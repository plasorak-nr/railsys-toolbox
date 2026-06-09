from rsys_analyser.analysis.exploration import get_valid_simulations, get_all_stations
from rsys_analyser.io.eval_manager import load

data = load('MRH S1 Eval Manager 2105.csv')


print(get_valid_simulations(data))
print(get_all_stations(data))