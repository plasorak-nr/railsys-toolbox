# Train Profiles

Pick one of the worst trains and inspect its median lateness profile and sectional running time (SRT) profile.

See the API documentation for each plot function:

- [`plot_median_lateness_profile`](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.plots.plot_median_lateness_profile)
- [`plot_median_runtime_profile`](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.plots.plot_median_runtime_profile)

??? hint "Hint"
    Start from the first row in `worst_n`, and use both `Train name` and `Operator Code` to build your selector.

??? example "Solution"
    First, build the selector in its own cell:

    ```python
    from rsys_toolbox.core import TrainSelector

    selected_train = worst_n.row(0, named=True)
    bad_headcode = selected_train["Train name"]
    bad_operator = selected_train["Operator Code"]

    bad_train_selector = TrainSelector(headcode=bad_headcode, operator_code=bad_operator)
    ```

    Then plot the median lateness profile in the next cell:

    ```python
    from rsys_toolbox.plots import plot_median_lateness_profile

    lateness_fig = plot_median_lateness_profile(base_data, train_selector=bad_train_selector)
    lateness_fig.savefig(f"median_lateness_profile_{bad_headcode}.png", dpi=150)
    plt.show()
    ```

    <figure>
      <img src="../images/median_lateness_profile_example.png" alt="Median lateness profile example" style="max-width:100%">
      <figcaption>Example median lateness profile for the worst train.</figcaption>
    </figure>

    Then plot the SRT (runtime) profile in another cell:

    ```python
    from rsys_toolbox.plots import plot_median_runtime_profile

    runtime_fig = plot_median_runtime_profile(base_data, train_selector=bad_train_selector)
    runtime_fig.savefig(f"median_runtime_profile_{bad_headcode}.png", dpi=150)
    plt.show()
    ```

    <figure>
      <img src="../images/median_runtime_profile_example.png" alt="Median runtime (SRT) profile example" style="max-width:100%">
      <figcaption>Example SRT profile for the worst train.</figcaption>
    </figure>

## (Cumulative) Histograms

Now zoom into a single station and train stops. Choose a station that appeared problematic in the profiles above and plot:

1. A histogram of **arrival lateness** across simulations for this train at that station.
2. A histogram of **dwell times** at that station.

Use a `LocationSelector` to filter to the station, and the [`plot_lateness_histogram`](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.plots.histogram.plot_lateness_histogram) and [`plot_dwell_histogram`](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.plots.histogram.plot_dwell_histogram) functions.

You can reuse your `TrainSelector` from the previous step.

??? hint "Hint"
    Pass `location_selector=LocationSelector(tiploc="BHAMNWS")` to restrict to Birmingham New Street.

??? example "Solution"
    ```python
    from rsys_toolbox.core import LocationSelector

    station_selector = LocationSelector(tiploc="BHAMNWS")
    ```

    Plot the lateness histogram in the next cell:

    ```python
    from rsys_toolbox.plots import plot_lateness_histogram

    lateness_hist = plot_lateness_histogram(base_data, location_selector=station_selector, train_selector=bad_train_selector, cumulative=True)
    lateness_hist.savefig("lateness_histogram_BHAMNWS.png", dpi=150)
    plt.show()
    ```

    <figure>
      <img src="../images/lateness_histogram_BHAMNWS.png" alt="Arrival lateness histogram at BHAMNWS" style="max-width:100%">
      <figcaption>Arrival lateness distribution at Birmingham New Street (BHAMNWS).</figcaption>
    </figure>

    Plot the dwell histogram in the next cell:

    ```python
    from rsys_toolbox.plots import plot_dwell_histogram

    dwell_hist = plot_dwell_histogram(base_data, location_selector=station_selector, train_selector=bad_train_selector)
    dwell_hist.savefig("dwell_histogram_BHAMNWS.png", dpi=150)
    plt.show()
    ```

    <figure>
      <img src="../images/dwell_histogram_BHAMNWS.png" alt="Dwell time histogram at BHAMNWS" style="max-width:100%">
      <figcaption>Dwell time distribution at Birmingham New Street (BHAMNWS).</figcaption>
    </figure>