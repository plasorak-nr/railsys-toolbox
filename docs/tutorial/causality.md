# Causality investigation
In this section, we will investigate correlation of trains between simulation. This will allow us to get an idea about the causality of a delay.

The relevant function is here: [`correlation_search`](https://networkrail-p-and-st.github.io/railsys-toolbox/api/#rsys_toolbox.analysis.correlation_search).

This function allows you to select causes and effects selector, and calculates the correlation between all the trains in it, let's see it in action

The first step is to get a train at a location, where you would expect another train to impact its lateness. Also, it's better to choose a train that has larger variations in lateness, we will call this train the effect, and we are looking for the cause.

```python
BAD_TIPLOC = "BHAMNWS"
EFFECT_ON_TRAIN = bad_train_selector

from rsys_toolbox.analysis import correlation_search
import polars as pl

# In here we are searching for correlation between events
csearch = correlation_search(
    base_data,
    train_effect_hypothesis=bad_train_selector,  # My train that is delayed...
    location_effect_hypothesis=LocationSelector(tiploc=BAD_TIPLOC),  # ... at Birmingham New Street,
    location_cause_hypothesis=LocationSelector(tiploc=BAD_TIPLOC),  # .... are there trains at Birmingham New Street that are also late...
    max_cause_window=timedelta(minutes=5),  # ... less than 5 min before my trains?
)

from rsys_toolbox.plots import plot_correlation_bars

fig = plot_correlation_bars(
    csearch,
    title=f"Delay candidate cause of: {bad_train_selector} at {BAD_TIPLOC}",
)
fig.savefig(f"correlation_at_BHAMNWS_{bad_train_selector.headcode}.png")
plt.show()
```

<figure>
    <img src="../images/correlation_at_BHAMNWS_1M41FX.png" alt="Correlations at BHAMNWS" style="max-width:100%">
    <figcaption>Example correlation at BHAMNWS</figcaption>
</figure>

All right, looks like 9G19EU is really correlated to our train! Let's have a look at it in more details

Lets use the [`correlation`](https://networkrail-p-and-st.github.io/railsys-toolbox/api/#rsys_toolbox.analysis.correlation) function to plot the delays together:

```python
from rsys_toolbox.analysis import correlation

MAYBE_CAUSE = "9G19EU"
result = correlation(
    base_data,
    location_cause_hypothesis=LocationSelector(tiploc=BAD_TIPLOC),
    location_effect_hypothesis=LocationSelector(tiploc=BAD_TIPLOC),
    train_cause_hypothesis=TrainSelector(headcode=MAYBE_CAUSE),  # The possible cause is 9G19EU
    train_effect_hypothesis=bad_train_selector,
    max_cause_window=timedelta(minutes=5),
)
plot_df = result.with_columns(
    (pl.col("Actual departure_cause") - pl.col("SchedDep_cause")).dt.total_seconds().alias("lateness_cause"),
    (pl.col("Actual departure_effect") - pl.col("SchedDep_effect")).dt.total_seconds().alias("lateness_effect"),
).filter((pl.col("lateness_cause") > 0) & (pl.col("lateness_effect") > 0))

plt.figure(figsize=(10, 5))

plt.scatter(plot_df.get_column("lateness_cause").to_list(), plot_df.get_column("lateness_effect").to_list(), alpha=0.7)
plt.xlabel(f"Lateness cause {MAYBE_CAUSE} at {BAD_TIPLOC} [seconds]")
plt.ylabel(f"Lateness effect {bad_train_selector.headcode} at {BAD_TIPLOC} [seconds]")
plt.title(f"1M41FX to {MAYBE_CAUSE} departure delay correlation at {BAD_TIPLOC}")
plt.grid(True)
plt.savefig("scatter_1M41FX_9G19EU_at_BHAMNWS.png")
plt.tight_layout()
```

<figure>
    <img src="../images/scatter_1M41FX_9G19EU_at_BHAMNWS.png" alt="Scatter plot: 1M41FX lateness V 9G19EU lateness" style="max-width:100%">
    <figcaption>Scatter plot: 1M41FX lateness V 9G19EU lateness</figcaption>
</figure>
