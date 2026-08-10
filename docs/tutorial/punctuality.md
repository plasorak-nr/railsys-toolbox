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
train_punctuality_at_worst_tiploc.write_csv('punctuality_data_worst_tiploc.csv')
# Or
# train_punctuality_at_worst_tiploc.write_excel('punctuality_data_worst_tiploc.xlsx')
```

!!! note "Want to plot the results?"
    You can use `matplotlib`:

    ```python
    import matplotlib.pyplot as plt

    worst_n = train_punctuality_at_worst_tiploc.head(20)

    labels = [
        f"{train} ({operator})"
        for train, operator in zip(
            worst_n.get_column("Train name").to_list(),
            worst_n.get_column("Operator Code").to_list(),
        )
    ]

    # Display percentages
    values = [value * 100 for value in worst_n.get_column("punctuality").to_list()]

    # And uncertainties!
    uncertainties = [value * 100 for value in worst_n.get_column("punctuality_uncertainty").to_list()]

    y_pos = range(len(labels))  # [0,1,2,...19]
    fig, ax = plt.subplots()

    # Create a horizontal bar plot. Values are percentages, and y_pos is the index of the train.
    ax.barh(list(y_pos), values, xerr=uncertainties, capsize=4)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Punctuality (%)")
    ax.set_title(f"20 worst trains at {worst_tiploc} (T-4.5 adherence)")
    ax.grid(axis="x", alpha=0.3)
    ax.invert_yaxis()  # Worst at the top.
    plt.tight_layout()
    ```