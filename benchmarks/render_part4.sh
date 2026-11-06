#!/bin/sh
# Renders every Part 4 deliverable. Run from the repository root:
#   sh docs/benchmarks/render_part4.sh
#
# Conventions, fixed across the whole set unless a row says otherwise:
#   -r 480 360   the resolution the reference images use (framing depends on it)
#   -l 4         the light-ray count the spec mandates for the sample sweep
#   -t 12        render threads on this machine
#   -R 1         Russian roulette on; the Task 2 bounce series passes -R 0
set -e
LOG=docs/benchmarks/part4.log
: > $LOG

run() {
  echo "=== pathtracer $* ===" >> $LOG
  { /usr/bin/time -p ./build/pathtracer "$@" ; } 2>&1 \
    | tr '\r' '\n' | grep -vE "Rendering\.\.\. [0-9]+%|^$" >> $LOG
}

S=1024
BUNNY=dae/sky/CBbunny.dae

# --- Global illumination showcase -------------------------------------------
run -t 12 -s $S -l 4 -m 5 -r 480 360 -f docs/images/part4_gi_bunny_1024.png $BUNNY
run -t 12 -s $S -l 4 -m 5 -r 480 360 -f docs/images/part4_gi_spheres_1024.png dae/sky/CBspheres_lambertian.dae
run -t 12 -s $S -l 4 -m 5 -r 480 480 -f docs/images/part4_gi_dragon_1024.png dae/sky/dragon.dae

# --- Direct versus indirect --------------------------------------------------
# Direct = zero bounce + one bounce. Indirect = everything past that, which is
# what -I suppresses the first two terms to isolate.
run -t 12 -s $S -l 4 -m 1 -o 1 -r 480 360 -f docs/images/part4_bunny_direct_1024.png $BUNNY
run -t 12 -s $S -l 4 -m 5 -o 1 -I -r 480 360 -f docs/images/part4_bunny_indirect_1024.png $BUNNY

# --- Task 2: isolated and accumulated bounces, fixed depth (no roulette) ----
for M in 0 1 2 3 4 5; do
  run -t 12 -s $S -l 4 -m $M -o 0 -R 0 -r 480 360 -f docs/images/part4_bunny_isolated_m${M}_1024.png $BUNNY
  run -t 12 -s $S -l 4 -m $M -o 1 -R 0 -r 480 360 -f docs/images/part4_bunny_accum_m${M}_1024.png $BUNNY
done

# --- Task 3: Russian roulette ------------------------------------------------
for M in 0 1 2 3 4 100; do
  run -t 12 -s $S -l 4 -m $M -o 1 -R 1 -r 480 360 -f docs/images/part4_bunny_rr_m${M}_1024.png $BUNNY
done

# --- Samples-per-pixel sweep, four light rays --------------------------------
for N in 1 2 4 8 16 64; do
  run -t 12 -s $N -l 4 -m 5 -r 480 360 -f docs/images/part4_bunny_spp${N}_l4.png $BUNNY
done
# The 1024-sample entry is the same configuration as the bunny showcase above.
cp docs/images/part4_gi_bunny_1024.png docs/images/part4_bunny_spp1024_l4.png
cp docs/images/part4_gi_bunny_1024_rate.png docs/images/part4_bunny_spp1024_l4_rate.png

echo "ALL PART 4 RENDERS COMPLETE" >> $LOG
