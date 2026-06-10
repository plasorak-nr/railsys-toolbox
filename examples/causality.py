"""An example of using the causality functionality of rsys_analyser."""

from datetime import timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from rsys_analyser.analysis.causality_investigation import LocationSelector, correlation
from rsys_analyser.io.eval_manager import load

data = load("assets/MRH S1 Eval Manager 2105.csv")

result = correlation(
	data,
	location_cause_hypothesis=LocationSelector(tiploc="BGRN T-1"),
	location_effect_hypothesis=LocationSelector(track="BGRN U-1"),
	max_cause_window=timedelta(minutes=10),
)

plot_df = result.with_columns(
	(pl.col("Actual departure_cause") - pl.col("SchedDep_cause")).dt.total_seconds().alias("lateness_cause"),
	(pl.col("Actual departure_effect") - pl.col("SchedDep_effect")).dt.total_seconds().alias("lateness_effect"),
).filter(
    (pl.col("lateness_cause") > 0) & (pl.col("lateness_effect") > 0)
)

print(
	plot_df.select(
		"Simulation no._effect",
		"Scheduled track_cause",
		"Scheduled track_effect",
		"Actual departure_cause",
		"Actual departure_effect",
		"lateness_cause",
		"lateness_effect",
	).head(20),
)

plt.figure(figsize=(10, 5))

plt.scatter(
    plot_df.get_column("lateness_cause").to_list(),
    plot_df.get_column("lateness_effect").to_list(),
    alpha=0.7
)
plt.xlabel("Lateness cause")
plt.ylabel("Lateness effect")

plt.title("BGRN T-2 to BGRN U-1 departure delay gap")
plt.grid(True, alpha=0.3)
plt.tight_layout()
output_path = "causality_departure_gap_scatter.png"
plt.savefig(output_path, dpi=150)
print(f"Saved plot to {output_path}")

print(f'Correlation {np.corrcoef(plot_df.get_column("lateness_cause").to_numpy(), plot_df.get_column("lateness_effect").to_numpy(),)}')
