# Punctuality

First, define punctuality and find the worst location in your simulations:

```python
from datetime import timedelta

T4m30s = timedelta(minutes=4, seconds=30)  # Best punctuality metric ever

from rsys_toolbox.analysis import punctuality

punctuality_data = punctuality(base_data, tolerance=T4m30s, exclude_deadlocks=True)
punctuality_data = punctuality_data.sort("punctuality", descending=False)  # We sort by increasing punctuality...
worst_row = punctuality_data.row(0, named=True)  # ... which means row[0] is now the worst in terms of punctuality
print(f"The worst punctuality station is {worst_row}")
```

Now print the worst trains at this worst TIPLOC.

??? hint "Hint"
    You shall need the `LocationSelector` again.

??? hint "Hint"
    The worst TIPLOC is stored in `worst_row["Station abbreviation"]`.

??? example "Solution"
    ```python
    from rsys_toolbox.core import LocationSelector

    worst_tiploc = worst_row["Station abbreviation"]
    worst_location = worst_row["Station name"]

    train_punctuality_at_worst_tiploc = punctuality(
        base_data,
        tolerance=T4m30s,
        group_by=["Train name", "Operator Code"],
        location_selector=LocationSelector(tiploc=worst_tiploc),
    )

    train_punctuality_at_worst_tiploc = train_punctuality_at_worst_tiploc.sort("punctuality", descending=False)

    worst_n = train_punctuality_at_worst_tiploc.head(20)

    print(worst_n)
    ```

Save your result to CSV.

```python
train_punctuality_at_worst_tiploc.write_csv("punctuality_data_worst_tiploc.csv")
# Or
# train_punctuality_at_worst_tiploc.write_excel('punctuality_data_worst_tiploc.xlsx')
```

!!! note "Want to plot the results?"
    You can use [`plot_train_punctuality`](https://plasorak-nr.github.io/railsys-toolbox/api/#rsys_toolbox.plots.punctuality.plot_train_punctuality):

    ```python
    import matplotlib.pyplot as plt
    from rsys_toolbox.plots import plot_train_punctuality

    fig = plot_train_punctuality(
        worst_n,
        location_name=worst_location,
        tiploc=worst_tiploc,
        tolerance=T4m30s,
    )
    output_plot = f"worst_trains_{worst_tiploc}.png"
    fig.savefig(output_plot, dpi=150)
    plt.show()
    ```

Example output generated from real data:

<img src="../images/worst_trains_real_data.png" alt="Punctuality chart generated from real Eval Manager data" width="1100" />