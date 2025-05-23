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
    print("Usage: python3 plot_l2_mpki_ipc.py <directory>")
    sys.exit(1)

log_dir = sys.argv[1]
if not os.path.isdir(log_dir):
    print(f"Error: {log_dir} is not a valid directory.")
    sys.exit(1)

log_files = glob.glob(os.path.join(log_dir, "*.out"))
if not log_files:
    print(f"No .out files found in {log_dir}")
    sys.exit(1)

mpki_vals, ipc_vals, benchmarks = [], [], []

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
        benchmarks.append(os.path.basename(file).replace(".out", ""))

# Plot MPKI
x = np.arange(len(benchmarks))
plt.figure(figsize=(14, 7))
plt.bar(x, mpki_vals, color='orange', edgecolor='black')
plt.xticks(x, benchmarks, rotation=60, ha='right')
plt.ylabel("L2 MPKI")
plt.title(f"L2 MPKI Across Benchmarks (Geomean: {geomean(mpki_vals):.2f})")
for i, v in enumerate(mpki_vals):
    plt.text(x[i], v / 2, f"{v:.2f}", ha='center', va='center', fontsize=9)
plt.tight_layout()
mpki_filename = input("Please provide a filename for the MPKI chart (e.g. mpki_output.png): ")
plt.savefig(mpki_filename, bbox_inches='tight')

# Plot IPC
plt.figure(figsize=(14, 7))
plt.bar(x, ipc_vals, color='skyblue', edgecolor='black')
plt.xticks(x, benchmarks, rotation=60, ha='right')
plt.ylabel("IPC")
plt.title(f"IPC Across Benchmarks (Geomean: {geomean(ipc_vals):.2f})")
for i, v in enumerate(ipc_vals):
    plt.text(x[i], v / 2, f"{v:.2f}", ha='center', va='center', fontsize=9)
plt.tight_layout()
ipc_filename = input("Please provide a filename for the IPC chart (e.g. ipc_output.png): ")
plt.savefig(ipc_filename, bbox_inches='tight')
