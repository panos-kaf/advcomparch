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

predictors_to_plot = ["  Nbit-", "  Static-", "  GlobalHistory-", "  LocalHistory-", "  Alpha21264", "  Tournament-"]
mpki_values = defaultdict(list)

# Selective compacting for Tournament predictors only
def extract_history_depth(name):
    for token in name.split('-'):
        if "History" in token:
            return token.replace("History", "")
    return "?"

def compact_tournament_name(full_name):
    if not full_name.startswith("Tournament-"):
        return full_name  # Leave others as-is

    parts = full_name.split('-')
    entries = parts[1] if len(parts) > 1 else "?"

    subparts = full_name.split('entries-')[-1].split('-vs-')
    if len(subparts) != 2:
        return f"Tourn{entries}:?"

    def shorten(subpred):
        if subpred.startswith("LocalHistory"):
            return "LocH" + extract_history_depth(subpred)
        elif subpred.startswith("GlobalHistory"):
            return "GlobH" + extract_history_depth(subpred)
        elif subpred.startswith("Nbit"):
            tokens = subpred.split('-')
            return "Nbit" + (tokens[1] if len(tokens) > 1 else '?')
        else:
            return "?"

    pred1 = shorten(subparts[0])
    pred2 = shorten(subparts[1])
    return f"Tourn{entries}:{pred1}vs{pred2}"


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

# Parse files and compute MPKI
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
                        raw_name = tokens[0].split(':')[0]
                        predictor_name = compact_tournament_name(raw_name)  # Only compress tournaments
                        correct_predictions = int(tokens[1])
                        incorrect_predictions = int(tokens[2])
                        mpki = incorrect_predictions / (total_ins / 1000.0)
                        mpki_values[predictor_name].append(mpki)

# Compute geometric mean MPKI
geomean_mpki = {}
for predictor, values in mpki_values.items():
    if all(v > 0 for v in values):
        log_sum = sum(math.log(v) for v in values)
        geomean = math.exp(log_sum / len(values))
        geomean_mpki[predictor] = geomean
    else:
        print(f"Warning: predictor {predictor} had zero or negative MPKI values, skipped.")

# Sort by name
predictors = geomean_mpki.keys()
geomean_values = [geomean_mpki[p] for p in predictors]
xAx = np.arange(len(predictors))

# Plotting
fig, ax = plt.subplots(figsize=(14, 7))
ax.grid(True)
ax.set_xticks(xAx)
ax.set_xticklabels(predictors, rotation=60, ha='right')
ax.set_ylabel("Average MPKI")
ax.set_title("Geometric Mean of MPKI Across Benchmarks")

bars = ax.bar(xAx, geomean_values, color="orange", edgecolor="black")
for i, val in enumerate(geomean_values):
    ax.text(xAx[i], val / 2, f"{val:.2f}", ha='center', va='center', fontsize=9, color='black')

plt.tight_layout()
filename = input("Please provide a filename for the produced file (e.g. output.png): ")
plt.savefig(filename, bbox_inches="tight")
