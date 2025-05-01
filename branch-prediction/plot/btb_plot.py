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

# Ensure directory is passed
if len(sys.argv) != 2:
    print("Usage: python3 btb_mpki_plot.py <directory>")
    sys.exit(1)

log_dir = sys.argv[1]

if not os.path.isdir(log_dir):
    print(f"Error: {log_dir} is not a valid directory.")
    sys.exit(1)

log_files = glob.glob(os.path.join(log_dir, "*.out"))
if not log_files:
    print(f"No .out files found in {log_dir}")
    sys.exit(1)

direction_mpki = defaultdict(list)
target_mpki = defaultdict(list)

for filename in log_files:
    with open(filename) as fp:
        total_ins = 0
        for line in fp:
            tokens = line.split()
            if line.startswith("Total Instructions:"):
                total_ins = int(tokens[2])
            elif line.startswith("  BTB-"):
                predictor_name = tokens[0].split(':')[0]
                correct = int(tokens[1])
                incorrect = int(tokens[2])
                target_correct = int(tokens[3])
                
                if total_ins == 0:
                    continue

                mpki_base = total_ins / 1000.0
                dir_mpki = incorrect / mpki_base
                tgt_mpki = (correct - target_correct) / mpki_base

                # Only include strictly positive values to avoid math domain error
                if dir_mpki > 0:
                    direction_mpki[predictor_name].append(dir_mpki)
                if tgt_mpki > 0:
                    target_mpki[predictor_name].append(tgt_mpki)

# Compute geometric mean MPKI for each
def geometric_mean(values):
    if not values:
        return float('nan')
    log_sum = sum(math.log(v) for v in values)
    return math.exp(log_sum / len(values))

predictors = sorted(set(direction_mpki.keys()) | set(target_mpki.keys()))
geo_dir_mpki = [geometric_mean(direction_mpki[p]) for p in predictors]
geo_tgt_mpki = [geometric_mean(target_mpki[p]) for p in predictors]

# Plotting
x = np.arange(len(predictors))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
bars1 = ax.bar(x - width/2, geo_dir_mpki, width, label='Direction MPKI', color='orange', edgecolor='black')
bars2 = ax.bar(x + width/2, geo_tgt_mpki, width, label='Target MPKI', color='skyblue', edgecolor='black')

ax.set_ylabel('Geometric Mean MPKI')
ax.set_title('BTB Predictors: Direction vs Target MPKI (Geometric Mean)')
ax.set_xticks(x)
ax.set_xticklabels(predictors, rotation=45)
ax.legend()
ax.grid(True, axis='y')

# Add value labels inside the bars
def add_labels(bars):
    for bar in bars:
        height = bar.get_height()
        if not math.isnan(height):
            ax.text(bar.get_x() + bar.get_width()/2, height / 2, f"{height:.2f}",
                    ha='center', va='center', fontsize=9, color='black')

add_labels(bars1)
add_labels(bars2)

filename = input("Please provide a filename for the produced file (e.g. btb_mpki.png): ")
plt.tight_layout()
plt.savefig(filename, bbox_inches="tight")