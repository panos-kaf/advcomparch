#!/usr/bin/env python3

import sys
import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Only interested in these predictors
predictors_to_plot = ["RAS-"]

# Ensure directory is passed
if len(sys.argv) != 2:
    print("Usage: python3 plot_mpki.py <directory>")
    sys.exit(1)

log_dir = sys.argv[1]

if not os.path.isdir(log_dir):
    print(f"Error: {log_dir} is not a valid directory.")
    sys.exit(1)

log_files = glob.glob(os.path.join(log_dir, "*.out"))
if not log_files:
    print(f"No .out files found in {log_dir}")
    sys.exit(1)

# Accumulators
mpki_totals = defaultdict(float)
counts = defaultdict(int)

for filename in log_files:
    with open(filename) as fp:
        total_ins = 0
        for line in fp:
            tokens = line.split()
            if line.startswith("Total Instructions:"):
                total_ins = int(tokens[2])
            else:
                for pred_prefix in predictors_to_plot:
                    if line.startswith(pred_prefix):
                        predictor_name = tokens[0].split(':')[0]
                        correct_predictions = int(tokens[1])
                        incorrect_predictions = int(tokens[2])
                        mpki = incorrect_predictions / (total_ins / 1000.0)
                        mpki_totals[predictor_name] += mpki
                        counts[predictor_name] += 1

# Compute average MPKI per predictor
predictors = sorted(mpki_totals.keys())
average_mpki = [mpki_totals[p] / counts[p] for p in predictors]

# Plotting
fig, ax = plt.subplots()
ax.grid(True)

xAx = np.arange(len(predictors))
ax.set_xticks(xAx)
ax.set_xticklabels(predictors, rotation=45)
ax.set_xlim(-0.5, len(predictors) - 0.5)
ax.set_ylim(min(average_mpki) - 0.05, max(average_mpki) + 0.05)
ax.set_ylabel("Average MPKI")
ax.bar(xAx, average_mpki, color="orange", edgecolor="black")

for i, val in enumerate(average_mpki):
    ax.text(
        xAx[i], val/2,            # halfway up the bar
        f"{val:.2f}",             # format the value
        ha='center', va='center', # center align
        fontsize=10, color='black', rotation=0
    )

plt.title("Atithmetic Mean of MPKI Across Benchmarks")
filename = input("Please provide a filename for the produced file (e.g. output.png): ")
plt.savefig(filename, bbox_inches="tight")