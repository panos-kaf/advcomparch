#!/usr/bin/env python3

import sys
import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import math
import re

def geomean(values):
    logs = [math.log(v) for v in values if v > 0]
    return math.exp(sum(logs) / len(logs)) if logs else 0

if len(sys.argv) != 2:
    print("Usage: python3 plot_l2.py <root_directory>")
    sys.exit(1)

root_dir = sys.argv[1]
if not os.path.isdir(root_dir):
    print(f"Error: {root_dir} is not a valid directory.")
    sys.exit(1)

subdirs = [d for d in sorted(os.listdir(root_dir)) if os.path.isdir(os.path.join(root_dir, d))]
if not subdirs:
    print(f"No subdirectories found in {root_dir}")
    sys.exit(1)

summary_mpki, summary_ipc, labels = [], [], []

for subdir in subdirs:
    full_path = os.path.join(root_dir, subdir)
    log_files = glob.glob(os.path.join(full_path, "*.out"))
    if not log_files:
        print(f"No .out files in {subdir}, skipping.")
        continue

    mpki_vals, ipc_vals = [], []
    for file in log_files:
        total_ins, l2_misses, ipc = 0, 0, 0.0
        with open(file) as f:
            for line in f:
                if line.startswith("Total Instructions:"):
                    total_ins = int(line.split(":")[1].strip())
                elif line.startswith("L2-Total-Misses:"):
                    l2_misses = int(line.split(":")[1].strip().split()[0])
                elif line.startswith("IPC:"):
                    ipc = float(line.split(":")[1].strip())
        if total_ins > 0:
            mpki = l2_misses / (total_ins / 1000)
            mpki_vals.append(mpki)
            ipc_vals.append(ipc)

    if mpki_vals and ipc_vals:
        summary_mpki.append(geomean(mpki_vals))
        summary_ipc.append(geomean(ipc_vals))
        labels.append(subdir)


# Function to extract tuple of ints for sorting (e.g. '1024_8_64' → (1024, 8, 64))
def extract_config_values(label):
    return tuple(int(x) for x in label.split('_'))

# Zip and sort based on config values
combined = sorted(zip(labels, summary_mpki, summary_ipc), key=lambda x: extract_config_values(x[0]))
labels, summary_mpki, summary_ipc = zip(*combined)

x = np.arange(len(labels))

filename = os.path.splitext(input('Enter file name (e.g. 4_2): ').lstrip('.'))[0]

# Plot summary MPKI
plt.figure(figsize=(14, 7))
plt.plot(x, summary_mpki, marker='x', linestyle='-', color='orange', markeredgecolor='black')
plt.xticks(x, labels, rotation=60, ha='right')
plt.ylabel("L2 MPKI (Geometric Mean)")
plt.title("MPKI by L2 Organization")
for i, v in enumerate(summary_mpki):
    plt.text(x[i] + 0.4, v, f"{v:.2f}", ha='center', va='bottom', fontsize=9)
plt.grid(True)
plt.tight_layout()
plt.savefig(filename+'_mpki.png', bbox_inches='tight')

# Plot summary IPC
plt.figure(figsize=(14, 7))
plt.plot(x, summary_ipc, marker='x', linestyle='-', color='green', markeredgecolor='black')
plt.xticks(x, labels, rotation=60, ha='right')
plt.ylabel("IPC (Geometric Mean)")
plt.title("IPC by L2 Organization")
for i, v in enumerate(summary_ipc):
    plt.text(x[i] + 0.4, v, f"{v:.2f}", ha='center', va='bottom', fontsize=9)
plt.grid(True)
plt.tight_layout()
plt.savefig(filename+'_ipc.png', bbox_inches='tight')

