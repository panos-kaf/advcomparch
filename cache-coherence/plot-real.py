import re
from collections import defaultdict
import matplotlib.pyplot as plt

def parse_file(filename):
    data = defaultdict(lambda: defaultdict(list))  # dict[grain][lock_type] = list of {threads, execution_time}
    pattern = re.compile(
        r"threads=(\d+)\s+\|\s+grain=(\d+)\s+\|\s+(real-locks-\S+)\s+\|\s+Execution time:(\d+\.\d+)"
    )

    with open(filename, 'r') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                threads = int(match.group(1))
                grain = int(match.group(2))
                lock_type = match.group(3).replace("real-locks-", "")
                execution_time = float(match.group(4))

                data[grain][lock_type].append({
                    'threads': threads,
                    'execution_time': execution_time
                })
    return data

import matplotlib.pyplot as plt

def plot_data(data):
    scales = ['linear', 'log']
    for yscale in scales:
        for grain, lock_groups in data.items():
            plt.figure(figsize=(8, 5))  # Start a new figure for each plot
            plt.yscale(yscale)
            plt.xscale('log', base=2)

            plt.title(f"Execution Time vs Threads (Grain = {grain}, yscale={yscale})")
            plt.xlabel("Threads")
            plt.ylabel("Execution Time (s)")

            for lock_type, entries in lock_groups.items():
                # Sort entries by thread count for smooth curves
                entries_sorted = sorted(entries, key=lambda x: x['threads'])
                threads = [e['threads'] for e in entries_sorted]
                times = [e['execution_time'] for e in entries_sorted]

                plt.plot(threads, times, marker='o', label=lock_type)

#plt.xticks([1, 2, 4, 8, 14], labels=[str(x) for x in [1, 2, 4, 8, 14]])
            threads = [e['threads'] for e in entries_sorted]
            plt.xticks(threads)

            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            output_dir = "graphs"
            plot_name = f"grain-{grain}-{yscale}-real-plot.png"
            plt.savefig(f"{output_dir}/{plot_name}")
            print(f'Saved plot: {plot_name} in ./{output_dir}')
            plt.close() 


if __name__ == "__main__":
    filename = "4.1.4.out"  
    result = parse_file(filename)
    plot_data(result)

