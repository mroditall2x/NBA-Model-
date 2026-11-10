set -e
v=$1; cd $(dirname $0)/$v
for d in 1028 1030 1031 1101 1102 1104 1105 1106 1107 1108; do
  D=2026-${d:0:2}-${d:2:2}
  python3 rot_blend.py $D 0.6 > slate/$d/rot.log 2>&1
  rm -f slate/$d/sim_*.parquet slate/$d/min_override.json
  export SAVE_SIM=1 NO_OUTGUESS=1
  python3 slate1021.py $D slate/$d > slate/$d/p1r.log 2>&1
  python3 blend_minutes.py slate/$d > /dev/null
  python3 slate1021.py $D slate/$d --blend > slate/$d/p2r.log 2>&1
  python3 card_slate.py slate/$d > /dev/null 2>&1
  echo "$v $d"
done
