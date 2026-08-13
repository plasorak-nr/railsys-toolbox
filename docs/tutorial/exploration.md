# Exploration

## Getting all the TIPLOCs
Let's write code to print all the TIPLOCs in this simulation. Create a new cell in your notebook, paste the code below, and execute it.

Bonus: We can also choose a station and display all its lines.

```python
from rsys_toolbox.analysis.exploration import get_all_stations

stations = get_all_stations(base_data)
print("All stations in the simulations:")
print(stations)

# Bonus
from rsys_toolbox.analysis.exploration import get_all_lines_at_station

print("All lines at Birmingam New Street:")
print(get_all_lines_at_station(base_data, "BHAMNWS"))  # Replace this with one from your list above.
```

## Get all Patterns and using a LocationSelector

Now explore the [documentation](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.analysis.get_all_patterns), and print all the patterns that call at a station.

??? hint "Hint"
    Use `rsys_toolbox.analysis.search_events` and `rsys_toolbox.core.LocationSelector` to filter the relevant events in your base data and feed it to the function that retrieves the all the patterns.

??? example "Solution"
    ```python
    from rsys_toolbox.analysis import get_all_patterns, search_events
    from rsys_toolbox.core import LocationSelector

    all_trains_bham = search_events(base_data, location_selector=LocationSelector(tiploc="BHAMNWS"))
    print("All patterns at Birmingham New Street:")
    print(get_all_patterns(all_trains_bham))
    ```


## Dumping a train information with a train selector
Choose a train pattern from above, and dump all its information for a simulation with [dump_train](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.analysis.dump_train).

??? example "Solution"
    ```python
    from rsys_toolbox.core import TrainSelector
    from rsys_toolbox.analysis import dump_train

    train_selector = TrainSelector(pattern="/EH/22180012/PLYMTH-BHAMNWS")

    # Create a dump of the train's journey
    train_log = dump_train(
        base_data,
        simulation=30,
        train_selector=train_selector,
    )
    print("/EH/22180012/PLYMTH-BHAMNWS train log:")
    print(train_log)
    ```

## Plotting a train graph
You can also plot a train graph with [`plot_train_graph`](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.plots.plot_train_graph), give it a go!

??? example "Solution"
	```python
	import polars as pl

	from rsys_toolbox.plots import plot_train_graph

	fig = plot_train_graph(base_data, simulation=30, train_selector=train_selector)
	fig.savefig(f"train_graph_sim_30.png")
	plt.show()
	```
    <figure>
        <img src="../images/train_graph_sim_30.png" alt="Train Graph for /EH/22180012/PLYMTH-BHAMNWS, simulation 30" style="max-width:100%">
        <figcaption>Train Graph for /EH/22180012/PLYMTH-BHAMNWS, simulation 30</figcaption>
    </figure>