#!/bin/bash

export LAUNCHER_DIR="$HOME/src/launcher"
export LAUNCHER_PLUGIN_DIR="$LAUNCHER_DIR/plugins"
export LAUNCHER_WORKDIR="$PWD"
export LAUNCHER_RMI="SLURM"
export LAUNCHER_SCHED="interleaved"
export LAUNCHER_JOB_FILE="unsplit.param"

echo "Starting launcher"
"$LAUNCHER_DIR/paramrun"
echo "Finished launcher"
