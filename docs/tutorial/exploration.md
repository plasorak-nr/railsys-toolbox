# Exploration

Let's write code to print all the TIPLOCs in this simulation. Create a new cell in your notebook, paste the code below, and execute it.

Bonus: We can also choose a station and display all its lines.

```python
from rsys_toolbox.analysis.exploration import get_all_stations

stations = get_all_stations(base_data)
print(stations)

# Bonus
from rsys_toolbox.analysis.exploration import get_all_lines_at_station

print(get_all_lines_at_station(base_data, "BHAMNWS"))  # Replace this with one from your list above.
```

Now explore the [documentation](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.analysis.get_all_patterns), and print all the patterns that call at a station.

??? hint "Hint"
    Use `rsys_toolbox.analysis.search_events` and `rsys_toolbox.core.LocationSelector` to filter the relevant events in your base data and feed it to the function that retrieves the all the patterns.

??? example "Solution"
    ```python
    from rsys_toolbox.analysis import get_all_patterns, search_events
    from rsys_toolbox.core import LocationSelector

    all_trains_bham = search_events(base_data, location_selector=LocationSelector(tiploc="BHAMNWS"))
    print(get_all_patterns(all_trains_bham))
    ```