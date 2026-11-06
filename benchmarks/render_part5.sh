#!/bin/sh
# Renders the Part 5 adaptive sampling deliverables. Run from the repo root:
#   sh docs/benchmarks/render_part5.sh
#
# The spec requires two scenes at >= 2048 max samples/pixel, one light ray, and
# max ray depth >= 5. Supplying -a is what enables adaptive sampling; -s then
# means the maximum sample count rather than a fixed one.
set -e
LOG=docs/benchmarks/part5.log
: > $LOG

run() {
  echo "=== pathtracer $* ===" >> $LOG
  { /usr/bin/time -p ./build/pathtracer "$@" ; } 2>&1 \
    | tr '\r' '\n' | grep -vE "Rendering\.\.\. [0-9]+%|^$" >> $LOG
}

run -t 12 -s 2048 -a 64 0.05 -l 1 -m 5 -r 480 360 \
    -f docs/images/part5_bunny_adaptive.png dae/sky/CBbunny.dae
run -t 12 -s 2048 -a 64 0.05 -l 1 -m 5 -r 480 360 \
    -f docs/images/part5_spheres_adaptive.png dae/sky/CBspheres_lambertian.dae

# Same budget without adaptive sampling, to quantify what the early exit saves.
run -t 12 -s 2048 -l 1 -m 5 -r 480 360 \
    -f docs/images/part5_bunny_fixed2048.png dae/sky/CBbunny.dae

echo "ALL PART 5 RENDERS COMPLETE" >> $LOG
