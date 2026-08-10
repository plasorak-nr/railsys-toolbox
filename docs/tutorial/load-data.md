# Load Data

Load the data with the `load` function from `rsys_toolbox`:

```python
from pathlib import Path
from rsys_toolbox.io.eval_manager import load

BASE_FILE = Path(r'C:\Users\plasora1\Network Rail\Performance & Simulation - Projects\2026 - Midlands Rail Hub\1. Cross City Service Uplifts\3. Technical\Multisims\Base\Archive\MRH Base Eval Manager 2905.csv')
base_data = load(BASE_FILE)
```

## First look at the data

Let's print how many simulations have deadlocked:

```python
from rsys_toolbox.analysis.exploration import get_valid_simulations

dls = get_valid_simulations(base_data, only_deadlocks=True)
print(f"There are {len(dls)} simulations that have deadlocked:")
for dl in dls:
    print("  -", dl)
```