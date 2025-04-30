#!/usr/bin/env python3

import sys
import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import math

predictors_to_plot = ["  Nbit-", "  BTB-"]
mpki_values = defaultdict(list)

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

# Parse files and collect MPKI
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
                        #print(tokens)
                        predictor_name = tokens[0].split(':')[0]
                        correct_predictions = int(tokens[1])
                        incorrect_predictions = int(tokens[2])
                        mpki = incorrect_predictions / (total_ins / 1000.0)
                        mpki_values[predictor_name].append(mpki)

# Compute geometric mean per predictor
geomean_mpki = {}
for predictor, values in mpki_values.items():
    if all(v > 0 for v in values):
        log_sum = sum(math.log(v) for v in values)
        geomean = math.exp(log_sum / len(values))
        geomean_mpki[predictor] = geomean
    else:
        print(f"Warning: predictor {predictor} had zero or negative MPKI values, skipped.")

predictors = sorted(geomean_mpki.keys())
geomean_values = [geomean_mpki[p] for p in predictors]
xAx = np.arange(len(predictors))

#Plotting
fig, ax = plt.subplots()
ax.grid(True)
ax.set_xticks(xAx)
ax.set_xticklabels(predictors, rotation=45)
ax.set_ylabel("Average MPKI")
ax.set_title("Geometric Mean of MPKI Across Benchmarks")
bars = ax.bar(xAx, geomean_values, color="orange", edgecolor="black")

for i, val in enumerate(geomean_values):
    ax.text(
        xAx[i], val/2,            # halfway up the bar
        f"{val:.2f}",             # format the value
        ha='center', va='center', # center align
        fontsize=10, color='black', rotation=0
    )

filename = input("Please provide a filename for the produced file (e.g. output.png): ")
plt.savefig(filename, bbox_inches="tight")