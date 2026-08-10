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
git clone https://github.com/plasorak-nr/railsys-toolbox.git
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

Now, go and explore the [documentation](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.analysis.exploration), and write code to print all the tiplocs in this simulation.

Bonus point, choose a station, and display all its lines.

??? example "Solution"
    ```python
    from rsys_toolbox.analysis.exploration import get_all_stations

    stations = get_all_stations(base_data)
    print(stations)

    # Bonus
    from rsys_toolbox.analysis.exploration import get_all_lines_at_station

    print(get_all_lines_at_station(base_data, "PADTON")) # Change that with one that is in your list above
    ```

Now print all the patterns that call at a station.

??? hint "Hint"
    Use a combination of `rsys_toolbox.analysis.search_events` and `rsys_toolbox.core.LocationSelector`.

??? example "Solution"
    ```python
    from rsys_toolbox.analysis.exploration import search_events,
    from rsys_toolbox.core import LocationSelector

    all_train_pdton = search_events(location_selector=LocationSelector(tiploc="PADTON"))
    print(get_all_patterns(all_train_pdton))
    ```

### Lets make stats!
First we defined what is the punctuality, and search the worst place in your simulations:
```python
from datetime import timedelta
T4m30s = timedelta(minutes=4, seconds=30) # Best punctuality metric ever

from rsys_toolbox.analysis import punctuality
punctuality_data = punctuality(base_data, tolerance=T4m30s, exclude_deadlocks=True)
punctuality_data = punctuality_data.sort("punctuality", descending=False) # We sort by increasing punctuality...
worst_row = punctuality_data.row(0, named=True) # ... which means row[0] is now the worst in terms of punctuality
print(f"The worst punctuality station is {worst_row}")
```

Now, print the worst trains at this worst TIPLOC.

??? hint "Hint"
    You shall need the `LocationSelector` again.

??? hint "Hint"
    To print the first  `LocationSelector` again.

??? example "Solution"
    ```python
    train_punctuality_at_PADTON = punctuality(
        data,
        tolerance=T4m30s,
        group_by=["Train name", "Operator Code"], # For now, we'll look at headcode/operator
        location_selector = LocationSelector(tiploc="PADTON") # I only want to see the arrivals at Manchester Airport
    )

    train_punctuality_at_PADTON = train_punctuality_at_PADTON.sort("punctuality", descending=False)

    worst_n = train_punctuality_at_PADTON.head(20)

    print(worst_n)
    ```

Save your result to csv!
```
train_punctuality_at_PADTON.write_csv('punctuality_data_PADTON.csv')
# Or
# train_punctuality_at_PADTON.write_excel('punctuality_data_PADTON.xlsx')
```

!!! note Want to plot the results?
    You can use `matplotlib`:
    ```python
    worst_n = punctuality_data.head(20)

    # I want to display: "station (tiploc)"
    labels = [f'{n} ({t})' for n, t in zip(worst_n.get_column("Station name").to_list(), worst_n.get_column("Station abbreviation").to_list())]

    # Display percentages
    values = [value * 100 for value in worst_n.get_column("punctuality").to_list()]

    # And uncertainties!
    uncertainties = [value * 100 for value in worst_n.get_column("punctuality_uncertainty").to_list()]

    y_pos = range(len(labels)) # [0,1,2,...19]
    fig, ax = plt.subplots()

    # create a horizontal bar plot. values are our percentages, and y_pos the index of the station
    ax.barh(list(y_pos), values, xerr=uncertainties, capsize=4)
    ax.set_yticks(list(y_pos)) # One tick per station
    ax.set_yticklabels(labels) # give our bars a name
    ax.set_xlabel("Punctuality (%)")
    ax.set_title("20 worst TIPLOCs (T-4.5 adherence)")
    ax.grid(axis="x", alpha=0.3)
    ax.invert_yaxis()  # worst at the top
    plt.tight_layout()
    ```