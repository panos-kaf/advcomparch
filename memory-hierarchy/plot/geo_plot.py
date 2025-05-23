#!/usr/bin/env python3

import sys
import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import math

def geomean(values):
    logs = [math.log(v) for v in values if v > 0]
    return math.exp(sum(logs) / len(logs)) if logs else 0

if len(sys.argv) != 2:
    print("Usage: python3 plot_l2_mpki_ipc.py <root_directory>")
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

# Plot summary MPKI
x = np.arange(len(labels))
plt.figure(figsize=(14, 7))
plt.bar(x, summary_mpki, color='orange', edgecolor='black')
plt.xticks(x, labels, rotation=60, ha='right')
plt.ylabel("L2 MPKI (Geomean)")
plt.title("Geometric Mean of L2 MPKI by Configuration")
for i, v in enumerate(summary_mpki):
    plt.text(x[i], v / 2, f"{v:.2f}", ha='center', va='center', fontsize=9)
plt.tight_layout()
mpki_filename = input("Filename for MPKI chart (e.g. mpki_summary.png): ")
plt.savefig(mpki_filename, bbox_inches='tight')

# Plot summary IPC
plt.figure(figsize=(14, 7))
plt.bar(x, summary_ipc, color='skyblue', edgecolor='black')
plt.xticks(x, labels, rotation=60, ha='right')
plt.ylabel("IPC (Geomean)")
plt.title("Geometric Mean of IPC by Configuration")
for i, v in enumerate(summary_ipc):
    plt.text(x[i], v / 2, f"{v:.2f}", ha='center', va='center', fontsize=9)
plt.tight_layout()
ipc_filename = input("Filename for IPC chart (e.g. ipc_summary.png): ")
plt.savefig(ipc_filename, bbox_inches='tight')

