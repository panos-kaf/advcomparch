#!/bin/bash

## Modify the following paths appropriately
BASE_DIR="/home/panos/dev/advcomparch/memory-hierarchy"
#BASE_DIR="/mnt/c/NTUA/advcomparch/memory-hierarchy" # windows

PIN_EXE="/home/panos/tools/pin/pin"
#PIN_EXE="/mnt/c/NTUA/tools/pin/pin" # windows
PIN_TOOL="$BASE_DIR/pintool/obj-intel64/simulator.so"
inputBase="$BASE_DIR/spec_benchmarks"

read -p "Enter output exercise directory (e.g. 5_4): " exer
mkdir -p "$BASE_DIR/output/$exer"

outDir="$BASE_DIR/output/$exer"

L1size=32
L1assoc=4
L1bsize=32

CONFS="256_4_256 512_4_256 1024_8_256 2048_16_256"

# Loop over every subfolder in the input base directory
for folder in "$inputBase"/*; do
    if [ -d "$folder" ]; then
        BENCH=$(basename "$folder")
        (
            cd "$folder" || { echo "Failed to enter $folder"; exit 1; }

            echo "=============================================="
            echo "Contents of speccmds.cmd for $BENCH:"
            echo "----------------------------------------------"
            head -n 1 speccmds.cmd
            echo "=============================================="
            echo ""

            line=$(head -n 1 speccmds.cmd)
            clean_cmd=$(echo "$line" | sed -n 's/.*\(\.\/.*\)/\1/p')

            for conf in $CONFS; do
                L2size=$(echo $conf | cut -d'_' -f1)
                L2assoc=$(echo $conf | cut -d'_' -f2)
                L2bsize=$(echo $conf | cut -d'_' -f3)

                # Create folder for this configuration
                confFolder="$outDir/$conf"
                mkdir -p "$confFolder/timing_logs"

                # Set output filename
                outFile=$(printf "%s.cslab_cache_stats_L2_LRU_%04d_%02d_%03d.out" "$BENCH" $L2size $L2assoc $L2bsize)
                pinOutFile="$confFolder/$outFile"

                pin_cmd="$PIN_EXE -t $PIN_TOOL -o $pinOutFile -L1c $L1size -L1a $L1assoc -L1b $L1bsize -L2c $L2size -L2a $L2assoc -L2b $L2bsize -- $clean_cmd"

                echo "PIN_CMD: $pin_cmd"

                { time /bin/bash -c "$pin_cmd" ; } &> "$confFolder/timing_logs/$outFile.time" &
            done

            wait
        ) &
    fi
done

wait
echo "All benchmarks done."

