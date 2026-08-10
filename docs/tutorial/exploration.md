# Exploration

Explore the [documentation](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.analysis.exploration), and write code to print all the TIPLOCs in this simulation.

Bonus point: choose a station and display all its lines.

??? example "Solution"
    ```python
    from rsys_toolbox.analysis.exploration import get_all_stations

    stations = get_all_stations(base_data)
    print(stations)

    # Bonus
    from rsys_toolbox.analysis.exploration import get_all_lines_at_station

    print(get_all_lines_at_station(base_data, "PADTON"))  # Replace this with one from your list above.
    ```

Now print all the patterns that call at a station.

??? hint "Hint"
    Use a combination of `rsys_toolbox.analysis.search_events` and `rsys_toolbox.core.LocationSelector`.

??? example "Solution"
    ```python
    from rsys_toolbox.analysis import get_all_patterns, search_events
    from rsys_toolbox.core import LocationSelector

    all_trains_padton = search_events(base_data, location_selector=LocationSelector(tiploc="PADTON"))
    print(get_all_patterns(all_trains_padton))
    ```