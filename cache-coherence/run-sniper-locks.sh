#!/bin/bash

base_dir="/root"
config="$base_dir/helpcode/ask3.cfg"
exe_dir="$base_dir/helpcode/exes"
sniper_exe="/root/sniper/run-sniper"
executables="sniper-locks-tas-ts sniper-locks-tas-cas sniper-locks-ttas-ts sniper-locks-ttas-cas sniper-locks-mutex"

# $4.1 
output_base="$base_dir/output/4.1"

iterations=1000
grain_sizes="1 10 100"
nthreads_list="1 2 4 8 16"

declare -A l2_shared_cores
l2_shared_cores[1]=1
l2_shared_cores[2]=2
l2_shared_cores[4]=4
l2_shared_cores[8]=4
l2_shared_cores[16]=1

declare -A l3_shared_cores
l3_shared_cores[1]=1
l3_shared_cores[2]=2
l3_shared_cores[4]=4
l3_shared_cores[8]=8
l3_shared_cores[16]=8

# overwrite with 4.2 configs
#source ./share-all.conf
#source ./share-l3.conf
source ./share-nothing.conf

for grain_size in $grain_sizes; do
	for nthreads in $nthreads_list; do
		for lock_type in $executables; do

			out_dir="$output_base/grain-${grain_size}/${nthreads}-core/$lock_type"
			mkdir -p $out_dir

            sniper_cmd="$sniper_exe -d $out_dir -c $config -n $nthreads --roi \
-c perf_model/l2_cache/shared_cores=${l2_shared_cores[$nthreads]} \
-c perf_model/l3_cache/shared_cores=${l3_shared_cores[$nthreads]} \
-- $exe_dir/$lock_type $nthreads $iterations $grain_size"

            echo "Running: $sniper_cmd"
            eval "$sniper_cmd"
        done
    done
done
