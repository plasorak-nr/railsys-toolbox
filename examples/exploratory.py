"""An example of using the exploratory functionality of rsys-toolbox."""

import polars as pl
from matplotlib.backends.backend_pdf import PdfPages

from rsys_toolbox.analysis import dump_train
from rsys_toolbox.core import TrainSelector
from rsys_toolbox.io.eval_manager import load
from rsys_toolbox.plots import plot_median_lateness_profile, plot_median_runtime_profile, plot_train_graph

TRAIN_NAME = "1V09DA"
SIM_NUMBER = 39

data = load(r"assets\20260512-MIAOpt-SimData_FullMIA.csv")

print(f"Considering {TRAIN_NAME}...")

candidate_rows = data.filter((pl.col("Simulation no.") == SIM_NUMBER) & (pl.col("Train name") == TRAIN_NAME))
if candidate_rows.is_empty():
    SIM_NUMBER = int(data.get_column("Simulation no.").unique().sort()[0])
    TRAIN_NAME = data.filter(pl.col("Simulation no.") == SIM_NUMBER).get_column("Train name").unique()[0]
    print(f"Fallback to Train {TRAIN_NAME} in simulation {SIM_NUMBER}")

# Example: Dump a train's journey for one simulation to a CSV file
# This creates a log of all stations a train visits with scheduled and actual times

train_selector = TrainSelector(headcode=TRAIN_NAME)

# Create a dump of the train's journey
train_log = dump_train(
    data,
    simulation=SIM_NUMBER,
    train_selector=train_selector,
)

# Save to CSV
output_path = f"train_dump_{TRAIN_NAME}_sim_{SIM_NUMBER}.csv"
train_log.write_csv(output_path)

fig = plot_train_graph(data, simulation=SIM_NUMBER, train_selector=train_selector)

runtime_fig = plot_median_runtime_profile(data, train_selector=train_selector)

lateness_fig = plot_median_lateness_profile(data, train_selector=train_selector)

# Save all figures to a multipage PDF
pdf_path = f"train_analysis_{TRAIN_NAME}.pdf"
with PdfPages(pdf_path) as pdf:
    pdf.savefig(fig, bbox_inches="tight")
    pdf.savefig(runtime_fig, bbox_inches="tight")
    pdf.savefig(lateness_fig, bbox_inches="tight")

print(f"Train {TRAIN_NAME} journey in simulation {SIM_NUMBER} saved to {output_path}")
print(f"All plots saved to {pdf_path}")
print(train_log)
