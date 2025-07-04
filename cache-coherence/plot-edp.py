import os
import re
import matplotlib.pyplot as plt

def extract_time_ns(sim_path):
    with open(sim_path) as f:
        for line in f:
            if line.strip().startswith("Time (ns)"):
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

for grain_dir in os.listdir(root_dir):
    if not grain_dir.startswith("grain-"):
        continue

    grain_path = os.path.join(root_dir, grain_dir)
    grain_data = {}

    for core_dir in os.listdir(grain_path):
        core_match = re.match(r"(\d+)-core", core_dir)
        if not core_match:
            continue
        num_cores = int(core_match.group(1))

        core_path = os.path.join(grain_path, core_dir)

        for lock_type in os.listdir(core_path):
            sim_path = os.path.join(core_path, lock_type, "sim.out")
            power_path = os.path.join(core_path, lock_type, "power.total.out")

            if not os.path.isfile(sim_path) or not os.path.isfile(power_path):
                continue

            time_ns = extract_time_ns(sim_path)
            energy = extract_energy(power_path)

            print (grain_dir, core_dir, lock_type, ':', time_ns, 'ns', ', energy:', energy)
                        
            if time_ns is None or energy is None:
                continue

            time_sec = time_ns * 1e-9

            if lock_type not in grain_data:
                grain_data[lock_type] = {
                    "cores": [],
                    "energy": [],
                    "edp": [],
                    "ed2p": [],
                    "ed3p": [],
                }
            edp = energy * time_sec
            ed2p = energy * time_sec**2
            ed3p = energy * time_sec**3

            grain_data[lock_type]["cores"].append(num_cores)
            grain_data[lock_type]["energy"].append(energy)
            grain_data[lock_type]["edp"].append(edp)
            grain_data[lock_type]["ed2p"].append(ed2p)
            grain_data[lock_type]["ed3p"].append(ed3p)

    if not grain_data:
        continue

    metrics = [("energy", "Energy (J)"),
               ("edp", "EDP (J·s)"),
               ("ed2p", "ED²P (J·s²)"),
               ("ed3p", "ED³P (J·s³)")]

    markers = ['<', '>', 'P', '*', 'x']
    
    scales = ['linear', 'log']
    for yscale in scales:
        for metric_key, ylabel in metrics:
            plt.figure(figsize=(10, 6))
            m_idx = 0
            for lock_type, data in grain_data.items():
                sorted_data = sorted(zip(data["cores"], data[metric_key]))
                cores, metric_values = zip(*sorted_data)
                plt.plot(cores, metric_values, marker=markers[m_idx % len(markers)],
                         label=lock_type)
                m_idx += 1
    
            plt.yscale(yscale)
            plt.xscale('log', base=2)
            plt.xlabel("Number of Cores")
            plt.ylabel(ylabel)
            plt.title(f"{ylabel} vs Cores — {grain_dir}")
            plt.xticks([1, 2, 4, 8, 16], labels=[str(x) for x in [1, 2, 4, 8, 16]])
            plt.legend()
            plt.grid(True, which="both", linestyle='-', linewidth=0.5)
            plt.tight_layout()
    
            output_file = f"{metric_key}-{grain_dir}-{yscale}-plot.png"
            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(f"{output_dir}/{output_file}")
            plt.close()
            print(f"Saved plot: {output_file} in ./{output_dir}")

