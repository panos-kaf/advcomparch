#!/bin/bash

exe_dir="/home/panos/dev/advcomparch/cache-coherence/helpcode/exes"
executables="real-locks-tas-ts real-locks-ttas-ts real-locks-tas-cas real-locks-ttas-cas"
read -p "enter output file name: " out_file

nthreads_list="1 2 4 8 14" # 14-core cpu
iterations="100000000"
grain_sizes="1 10 100"

> "$out_file"  # Clear output file

for grain_size in $grain_sizes; do 
    for locks in $executables; do
        for nthreads in $nthreads_list; do
            
			echo "running: ${exe_dir}/${locks} ${nthreads} ${iterations} ${grain_size}" 
			result=$("$exe_dir/$locks" "$nthreads" "$iterations" "$grain_size")
            
            echo -e "threads=$nthreads \t| grain=$grain_size\t| $locks \t| $result" >> "$out_file"
        done
    done
done
