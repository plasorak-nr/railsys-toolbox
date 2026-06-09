from rsys_analyser.analysis.exploration import (
    get_valid_simulations,
    get_all_stations,
    get_all_lines_at_station,
    get_all_operator_codes,
    get_all_service_codes,
    get_all_patterns,
    get_all_train_numbers,
    get_all_train_names,
    get_all_train_classes,
    get_all_train_categories,
    get_all_train_formations,
)
from rsys_analyser.io.eval_manager import load

data = load("assets/MRH S1 Eval Manager 2105.csv")


print("get_valid_simulations", get_valid_simulations(data))
print("get_all_lines_at_station", get_all_lines_at_station(data, "SELYOAK"))
print("get_all_stations", get_all_stations(data))
print("get_all_operator_codes", get_all_operator_codes(data))
print("get_all_service_codes", get_all_service_codes(data))
print("get_all_patterns", get_all_patterns(data))
print("get_all_train_numbers", get_all_train_numbers(data))
print("get_all_train_names", get_all_train_names(data))
print("get_all_train_classes", get_all_train_classes(data))
print("get_all_train_categories", get_all_train_categories(data))
print("get_all_train_formations", get_all_train_formations(data))
