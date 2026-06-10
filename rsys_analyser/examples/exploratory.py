"""An example of using the exploratory functionality of rsys-analyser."""

from pathlib import Path

from rsys_analyser.analysis.exploration import dump_train
from rsys_analyser.core import TrainSelector
from rsys_analyser.io.eval_manager import load
from rsys_analyser.plots import plot_train_graph

data = load("assets/MRH S1 Eval Manager 2105.csv")

# Example: Dump a train's journey for one simulation to a CSV file
# This creates a log of all stations a train visits with scheduled and actual times

# Get the first valid simulation number
first_sim = data.get_column("Simulation no.").unique().sort()[0]

# Get the first train in that simulation
first_train = data.filter(data["Simulation no."] == first_sim).get_column("Train no.").unique()[0]

# Create a dump of the train's journey
train_log = dump_train(
    data,
    simulation=first_sim,
    train_filter=TrainSelector(train_number=first_train),
)

# Save to CSV
output_path = Path(__file__).resolve().parents[2] / "train_dump.csv"
train_log.write_csv(output_path)

fig = plot_train_graph(train_log, speed_kmh=100.0)
figure_path = Path(__file__).resolve().parents[2] / "train_graph.png"
fig.savefig(figure_path, dpi=150)

print(f"Train {first_train} journey in simulation {first_sim} saved to {output_path}")
print(f"Train graph saved to {figure_path}")
print(train_log)
