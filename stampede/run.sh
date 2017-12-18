#!/bin/bash

#SBATCH -A iPlant-Collabs
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -J cntfltr
#SBATCH -p normal
#SBATCH -t 24:00:00

set -u

export LAUNCHER_DIR="$HOME/src/launcher"
export LAUNCHER_PLUGIN_DIR="$LAUNCHER_DIR/plugins"
export LAUNCHER_WORKDIR="$PWD"
export LAUNCHER_RMI=SLURM
export LAUNCHER_SCHED=interleaved

IMG="centrifuge-filter-0.0.1.img"
FILTER="singularity exec $IMG filter.py"

EXCLUDE=""
SPLIT_DIR=""
REPORTS_DIR=""
OUT_DIR="$PWD/centrifuge-filter/accepted"
EXCLUDE_DIR="$PWD/centrifuge-filter/excluded"

#EXCLUDE="\"Trichodesmium,Trichodesmium erythraeum,Homo sapiens,human\""
#SPLIT_DIR="$WORK/tricho/paired-centrifuge/split"
#REPORTS_DIR="$WORK/tricho/paired-centrifuge/reports"
#OUT_DIR="$PWD/centrifuge-filter/accepted"
#EXCLUDE_DIR="$PWD/centrifuge-filter/excluded"

function lc() {
  wc -l "$1" | cut -d ' ' -f 1
}

function HELP() {
  printf "Usage:\n  %s -e human -s SPLIT -e REPORTS\n\n" "$(basename "$0")"

  echo "Required arguments:"
  echo " -s SPLIT_DIR (dir of split files for Centrifuge)"
  echo " -r REPORTS_DIR (dir of report files from Centrifuge)"
  echo " -e EXLUDE (list of species/taxids to exclude)"
  echo ""
  echo "Options (default in parentheses):"
  echo " -o OUT_DIR ($OUT_DIR)"
  echo " -x EXCLUDE_DIR ($EXCLUDE_DIR)"
  echo ""
  exit 0
}

if [[ $# -eq 0 ]]; then
  HELP
fi

while getopts :e:r:s:o:x:h OPT; do
  case $OPT in
    e)
      EXCLUDE="$OPTARG"
      ;;
    h)
      HELP
      ;;
    r)
      REPORTS_DIR="$OPTARG"
      ;;
    s)
      SPLIT_DIR="$OPTARG"
      ;;
    o)
      OUT_DIR="$OPTARG"
      ;;
    x)
      EXCLUDE_DIR="$OPTARG"
      ;;
    :)
      echo "Error: Option -$OPTARG requires an argument."
      exit 1
      ;;
    \?)
      echo "Error: Invalid option: -${OPTARG:-""}"
      exit 1
  esac
done

if [[ -z "$EXCLUDE" ]]; then
    echo "EXCLUDE cannot be empty"
    exit 1
fi

if [[ ! -d "$SPLIT_DIR" ]]; then
    echo "SPLIT_DIR \"$SPLIT_DIR\" not a directory"
    exit 1
fi

if [[ ! -d "$REPORTS_DIR" ]]; then
    echo "REPORTS_DIR \"$REPORTS_DIR\" not a directory"
    exit 1
fi

[[ ! -d "$OUT_DIR" ]] && mkdir -p "$OUT_DIR"
[[ ! -d "$EXCLUDE_DIR" ]] && mkdir -p "$EXCLUDE_DIR"

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

NJOBS=$(lc "$PARAM")
if [[ $NJOBS -lt 1 ]]; then
    echo "No jobs to run?"
    exit 1
fi

echo "Launching NJOBS \"$NJOBS\" $(date)"
export LAUNCHER_JOB_FILE="$PARAM"
[[ $NUM -gt 7 ]] && export LAUNCHER_PPN=8
[[ $NUM -gt 3 ]] && export LAUNCHER_PPN=4
"$LAUNCHER_DIR/paramrun"

echo "Finished LAUNCHER $(date)"
echo ""
echo "Comments to kyclark@email.arizona.edu"
