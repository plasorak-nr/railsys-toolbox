# Tutorial

## Aim

In this tutorial, you are going to use the Midlands Rail Hub project data which contains a base and 5 options. You are encouraged to use something in your current project, as long as you have ran it in `EvalManager`. We will investigate:
- What are the worst stations in term of punctuality,
- See some train-level SRTs and punctuality data to try to identify the trains that make up most of these delays,
- Try to identify if these delays are caused by other trains
- And maybe, identify flighting problems.

## What you will need

- Access to this repo
- uv/python
- VS Code.


## Setup

Head over to a PowerShell terminal and type:
```PowerShell
git clone <this>
uv init rsys-toolbox-tutorial  # Or whatever else you want to call it
cd rsys-toolbox-tutorial
code .
```

Now navigate to pyproject.toml, add the following section:

```yaml
[project]
# ...
# let whatever you have here
# ...
[project]
dependencies = [
    "rsys-toolbox",
]

[tool.uv.sources]
rsys-toolbox = { path = "../rsys-analyser", editable = true }
```

Then, back in your terminal:
```PowerShell
uv venv
uv sync
```

## Let's start!
Create a new python notebook in the root of your directory, name it `tutorial.ipynb` (the extension is the important piece here).


### Load the data
This is done with the `load` function in `rsys_toolbox`:
```python
from pathlib import Path
from rsys_toolbox.io.eval_manager import load

BASE_FILE = Path(r'C:\Users\plasora1\Network Rail\Performance & Simulation - Projects\2026 - Midlands Rail Hub\1. Cross City Service Uplifts\3. Technical\Multisims\Base\Archive\MRH Base Eval Manager 2905.csv')
base_data = load(BASE_FILE)
```

### First look at the data
Let's print how many simulations have deadlocked:

```python
from rsys_toolbox.analysis.exploration import get_valid_simulations

dls = get_valid_simulations(base_data, only_deadlocks=True)
print(f"There are {len(dls)} simulations that have deadlocked:")
for dl in dls:
    print("  -", dl)
```

Now, go and explore the documentation, and write code to print all the tiplocs in this simulation

??? success "Solution"
    ```python
    from rsys_toolbox.analysis.exploration import get_all_stations

    stations = get_all_stations(base_data)
    print(stations)
    ```