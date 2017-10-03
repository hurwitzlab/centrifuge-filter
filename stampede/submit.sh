#!/bin/bash

set -u

#sbatch -A iPlant-Collabs -N 1 -n 1 -t 24:00:00 -p normal -J fltrcent run.sh
sbatch -A iPlant-Collabs -N 1 -n 1 -t 24:00:00 -p normal -J kornunsp korn-unsplit.sh
