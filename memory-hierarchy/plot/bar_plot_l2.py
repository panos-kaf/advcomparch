#!/usr/bin/env python3

import sys
import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import math

caches = ['lru', 'random', 'lfu', 'lip', 'srrip_hp', 'srrip_fp']

def geomean(values):
    logs = [math.log(v) for v in values if v > 0]
    return math.exp(sum(logs) / len(logs)) if logs else 0

def extract_config_values(label):
    return tuple(int(x) for x in label.split('_') if x.isdigit())

if len(sys.argv) != 2:
    print("Usage: python3 plot_l2.py <root_directory>")
    sys.exit(1)

root_dir = sys.argv[1]
if not os.path.isdir(root_dir):
    print(f"Error: {root_dir} is not a valid directory.")
    sys.exit(1)

# config_data[config][cache] = (mpki, ipc)
config_data = {}

for cache in caches:
    cache_path = os.path.join(root_dir, cache)
    if not os.path.isdir(cache_path):
        print(f"Skipping '{cache}': directory not found.")
        continue

    subdirs = [d for d in sorted(os.listdir(cache_path)) if os.path.isdir(os.path.join(cache_path, d))]

    for config in subdirs:
        full_path = os.path.join(cache_path, config)
        log_files = glob.glob(os.path.join(full_path, "*.out"))
        if not log_files:
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
            if config not in config_data:
                config_data[config] = {}
            config_data[config][cache] = (geomean(mpki_vals), geomean(ipc_vals))

# Sort configs numerically
sorted_configs = sorted(config_data.keys(), key=extract_config_values)
num_configs = len(sorted_configs)
num_caches = len(caches)

# Prepare data
mpki_matrix = []
ipc_matrix = []

for cache in caches:
    mpki_row = []
    ipc_row = []
    for config in sorted_configs:
        mpki, ipc = config_data.get(config, {}).get(cache, (0, 0))
        mpki_row.append(mpki)
        ipc_row.append(ipc)
    mpki_matrix.append(mpki_row)
    ipc_matrix.append(ipc_row)

x = np.arange(num_configs)
bar_width = 0.15
offsets = np.linspace(-bar_width*num_caches/2, bar_width*num_caches/2, num_caches)

filename = os.path.splitext(input('Enter file name (e.g. 4_3): ').lstrip('.'))[0]

# Plot MPKI
plt.figure(figsize=(14, 7))
for i, cache in enumerate(caches):
    bars = plt.bar(x + offsets[i], mpki_matrix[i], width=bar_width, label=cache.upper(), edgecolor='black')
    for j, bar in enumerate(bars):
        height = bar.get_height()
        if height > 0:
            plt.text(bar.get_x() + bar.get_width() / 2, height / 2,
                     f"{height:.2f}", ha='center', va='center', fontsize=9)

plt.xticks(x, sorted_configs, rotation=60, ha='right')
plt.ylabel("L2 MPKI (Geometric Mean)")
plt.title("L2 MPKI Comparison by Cache Organization and Replacement Strategy ")
plt.legend()
plt.tight_layout()
plt.savefig(filename+'_mpki.png', bbox_inches='tight')

# Plot IPC
plt.figure(figsize=(14, 7))
for i, cache in enumerate(caches):
    bars = plt.bar(x + offsets[i], ipc_matrix[i], width=bar_width, label=cache.upper(), edgecolor='black')
    for j, bar in enumerate(bars):
        height = bar.get_height()
        if height > 0:
            plt.text(bar.get_x() + bar.get_width() / 2, height / 2,
                     f"{height:.2f}", ha='center', va='center', fontsize=9)

plt.xticks(x, sorted_configs, rotation=60, ha='right')
plt.ylabel("IPC (Geometric Mean)")
plt.title("IPC Comparison by Cache Organization and Replacement Strategy")
plt.legend()
plt.tight_layout()
plt.savefig(filename+'_ipc.png', bbox_inches='tight')

