#!/usr/bin/env bash
set -e

mkdir -p out
for tcp in Tahoe Reno Vegas; do
  for seed in $(seq 1 10); do
    echo "Running $tcp seed=$seed"
    ns phase2.tcl $tcp $seed out/${tcp}_${seed}
  done
done
echo "Done."
