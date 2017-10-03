#!/bin/bash

set -u

BASE_DIR="$SCRATCH/frischkorn/centrifuge"
EXCLUDE="\"Trichodesmium,Trichodesmium erythraeum,Homo sapiens,human\""

#BASE_DIR="$WORK/pam-morris/centrifuge"
#EXCLUDE="\"Homo sapiens,human\""

SPLIT_DIR="$BASE_DIR/split"
REPORTS_DIR="$BASE_DIR/reports"
OUT_DIR="$BASE_DIR/filtered"
EXCLUDE_DIR="$BASE_DIR/excluded"
FILTER="$WORK/misc/filter-centrifuge/filter.py"

SPLIT_FILES=$(mktemp)
find "$SPLIT_DIR" -type f > "$SPLIT_FILES"
NUM=$(wc -l "$SPLIT_FILES" | awk '{print $1}')
printf "There are %s split files\n" "$NUM"

PARAM="$$.param"
cat /dev/null > "$PARAM"

i=0
while read -r FILE; do
  let i++
  BASENAME=$(basename "$FILE")
  printf "%5d: %s\n" "$i" "$BASENAME"

  SUM_FILE="$REPORTS_DIR/$BASENAME.sum"
  if [[ -s "$SUM_FILE" ]]; then
    echo "$FILTER -f $FILE -s $SUM_FILE -e $EXCLUDE -o $OUT_DIR -x $EXCLUDE_DIR" >> "$PARAM"
  else
    echo "Missing SUM_FILE \"$SUM_FILE\""
  fi
done < "$SPLIT_FILES"

echo "Launching with \"$PARAM\""
export LAUNCHER_DIR="$HOME/src/launcher"
export LAUNCHER_PLUGIN_DIR="$LAUNCHER_DIR/plugins"
export LAUNCHER_WORKDIR="$PWD"
export LAUNCHER_JOB_FILE="$PARAM"
export LAUNCHER_RMI=SLURM
export LAUNCHER_SCHED=interleaved
export LAUNCHER_PPN=8
"$LAUNCHER_DIR/paramrun"
echo "Finished LAUNCHER"
