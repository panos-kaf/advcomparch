#!/bin/bash

bench_dir="/root/output/4.2"
mcpat="/root/sniper/tools/advcomparch_mcpat.py"

find "$bench_dir" -type d | while read dir; do
    if [ -f "$dir/sim.out" ]; then
        cmd="$mcpat -d \"$dir\" -t total -o \"$dir/power\" > \"$dir/power.total.out\""
        echo "Running: $cmd"
        eval $cmd
    fi
done
