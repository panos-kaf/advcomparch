import os
import re
import matplotlib.pyplot as plt

root_dir = input('Enter benchmark directory:')
output_dir = input('Enter output directory:')

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
            if not os.path.isfile(sim_path):
                continue

            with open(sim_path) as f:
                lines = f.readlines()

            cycles_line = next((line for line in lines if line.strip().startswith("Cycles")), None)
            if not cycles_line:
                continue

            cycle_values = list(map(int, re.findall(r"\d+", cycles_line)))
            if not cycle_values:
                continue
            
            total_cycles = cycle_values[0]

            if lock_type not in grain_data:
                grain_data[lock_type] = {"cores": [], "total_cycles": []}
            grain_data[lock_type]["cores"].append(num_cores)
            grain_data[lock_type]["total_cycles"].append(total_cycles)

    # Plot for current grain
    if not grain_data:
        continue

    #print(grain_data)
    
    scales = ['linear', 'log']

    for yscale in scales:
        markers = ['<', '>', 'P', '*', 'x']
        plt.figure(figsize=(10, 6))
        for lock_type, values in grain_data.items():
            sorted_data = sorted(zip(values["cores"], values["total_cycles"]))
            cores, total_cycles = zip(*sorted_data)
            plt.plot(cores, total_cycles, marker=markers.pop(0), label=lock_type)
    
        plt.yscale(yscale)
        plt.xscale('log',base=2)
        plt.xlabel("Number of Cores")
        plt.ylabel("Total Cycles")
        plt.title(f"Total Cycles vs Cores — {grain_dir}")
        plt.xticks([1, 2, 4, 8, 16], labels=[str(x) for x in [1, 2, 4, 8, 16]])
        plt.legend()
        plt.grid(True, which="both", linestyle='-', linewidth=0.5)
        plt.tight_layout()
    
    
        # Save as PNG
        output_file = f"{grain_dir}-{yscale}-plot"
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(f"{output_dir}/{output_file}.svg", format='svg')
        plt.savefig(f"{output_dir}/{output_file}.png", format='png')
        plt.close()
    
        print(f"Saved plot: {output_file} in ./{output_dir}")

