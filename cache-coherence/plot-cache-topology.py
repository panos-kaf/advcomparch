import os
import re
import matplotlib.pyplot as plt
import numpy as np

def extract_time_ns(sim_path):
    with open(sim_path) as f:
        for line in f:
            if line.strip().startswith("Time (ns)"):
                values = list(map(int, re.findall(r"\d+", line)))
                return values[0] if values else None
    return None

def extract_cycles(sim_path):
    with open(sim_path) as f:
        for line in f:
            if line.strip().startswith("Cycles"):
                values = list(map(int, re.findall(r"\d+", line)))
                return values[0] if values else None
        return None

def extract_energy(power_path):
    with open(power_path) as f:
        for line in f:
            if line.strip().startswith("total"):
                match = re.search(r"total\s+[\d.]+ W\s+([\d.]+)\s+([mμk]?J)", line)
                if match:
                    value = float(match.group(1))
                    unit = match.group(2)
                    multiplier = {
                        "kJ": 1e3,
                        "J": 1,
                        "mJ": 1e-3,
                        "μJ": 1e-6,
                    }[unit]
                    return value * multiplier
    return None

root_dir = input('Enter benchmark directory: ')
output_dir = input('Enter output directory: ')

# Dictionary to store data for each cache architecture
cache_arch_data = {}

# Look for all subdirectories (cache architectures)
for cache_arch in os.listdir(root_dir):
    cache_arch_path = os.path.join(root_dir, cache_arch)
    if not os.path.isdir(cache_arch_path):
        continue
    
    print(f"Processing cache architecture: {cache_arch}")
    
    # Look for grain-1/4-core/lock-type structure
    grain_1_path = os.path.join(cache_arch_path, "grain-1")
    if not os.path.isdir(grain_1_path):
        print(f"  No grain-1 directory found in {cache_arch}")
        continue
    
    core_4_path = os.path.join(grain_1_path, "4-core")
    if not os.path.isdir(core_4_path):
        print(f"  No 4-core directory found in {cache_arch}/grain-1")
        continue
    
    cache_arch_data[cache_arch] = {}
    
    # Look for lock types
    for lock_type in os.listdir(core_4_path):
        lock_path = os.path.join(core_4_path, lock_type)
        if not os.path.isdir(lock_path):
            continue
        
        sim_path = os.path.join(lock_path, "sim.out")
        power_path = os.path.join(lock_path, "power.total.out")
        
        if not os.path.isfile(sim_path) or not os.path.isfile(power_path):
            print(f"  Missing files for {cache_arch}/grain-1/4-core/{lock_type}")
            continue
        
        cycles = extract_cycles(sim_path)
        time_ns = extract_time_ns(sim_path)
        energy = extract_energy(power_path)
        
        print(f"  {cache_arch} - {lock_type}: {time_ns} ns, energy: {energy} J")
        
        if time_ns is None or energy is None:
            print(f"  Could not extract data for {cache_arch}/grain-1/4-core/{lock_type}")
            continue
        
        time_sec = time_ns * 1e-9
        
        # Calculate metrics
        edp = energy * time_sec
        ed2p = energy * time_sec**2
        ed3p = energy * time_sec**3
        
        cache_arch_data[cache_arch][lock_type] = {
            "cycles": cycles,
            "energy": energy,
            "edp": edp,
            "ed2p": ed2p,
            "ed3p": ed3p
        }

# Create bar plots for each metric and lock type
if not cache_arch_data:
    print("No data found!")
    exit()

# Get all unique lock types
all_lock_types = set()
for arch_data in cache_arch_data.values():
    all_lock_types.update(arch_data.keys())
all_lock_types = sorted(list(all_lock_types))

metrics = [("cycles", "Cycles"),
           ("energy", "Energy (J)"),
           ("edp", "EDP (J·s)"),
           ("ed2p", "ED²P (J·s²)"),
           ("ed3p", "ED³P (J·s³)")]

# Create plots for each metric
for metric_key, ylabel in metrics:
    plt.figure(figsize=(12, 8))
    
    # Prepare data for bar plot
    cache_archs = list(cache_arch_data.keys())
    n_archs = len(cache_archs)
    n_locks = len(all_lock_types)
    
    # Set up bar positions
    bar_width = 0.8 / n_locks
    x = np.arange(n_archs)
    
    # Create bars for each lock type
    for i, lock_type in enumerate(all_lock_types):
        values = []
        for arch in cache_archs:
            if lock_type in cache_arch_data[arch]:
                values.append(cache_arch_data[arch][lock_type][metric_key])
            else:
                values.append(0)  # Or np.nan if you prefer
        
        offset = (i - n_locks/2 + 0.5) * bar_width
        plt.bar(x + offset, values, bar_width, label=lock_type, alpha=0.8)
    
    plt.xlabel("Cache Architecture")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} Comparison Across Cache Architectures (grain-1, 4-core)")
    plt.xticks(x, cache_archs, ha='right')
    plt.legend()
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    
    # Save plot
    output_file = f"{metric_key}-cache-arch-plot"
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f"{output_dir}/{output_file}.png", format='png', dpi=300, bbox_inches='tight')
    plt.savefig(f"{output_dir}/{output_file}.svg", format='svg', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved plot: {output_file} in ./{output_dir}")

    

print("\nAll plots have been generated!")
