# Part 2: BVH benchmark results

Measured on this ARM64 Mac with a Release build, one render thread, one sample per pixel, and 480 × 360 output. Times below are the renderer’s reported render time, excluding scene loading and BVH construction. These are single-run measurements, not averaged benchmarks.

| Scene | Primitives | Brute force (s) | BVH (s) | Speedup | Primitive tests/ray: before → after | BVH build (s) |
|---|---:|---:|---:|---:|---:|---:|
| cow | 5,856 | 1.9472 | 0.0259 | 75.2× | 5856 → 3.13 | 0.0015 |
| beetle | 7,558 | 2.2976 | 0.0298 | 77.1× | 7558 → 3.78 | 0.0019 |
| banana | 2,458 | 0.6962 | 0.0288 | 24.2× | 2458 → 4.73 | 0.0005 |

For all three comparisons, the BVH PNG is byte-for-byte identical to its brute-force PNG. Single-thread rendering keeps the random sampling sequence consistent between runs. Raw logs are stored beside this file. Baseline images and the pre-BVH executable are retained locally under `build/part2-baseline/` and `build/pathtracer_bruteforce`.

## Larger scenes

| Scene | Primitives | BVH render (s) | BVH build (s) | Primitive tests/ray |
|---|---:|---:|---:|---:|
| maxplanck | 50,801 | 0.0435 | 0.0157 | 4.33 |
| lucy | 133,796 | 0.0595 | 0.0440 | 6.59 |

## Reproduce a render

Run from the repository root:

```sh
./build/pathtracer -t 1 -s 1 -r 480 360 \
  -f docs/images/part2_cow.png dae/meshedit/cow.dae
```

Use `build/pathtracer_bruteforce` with the same arguments and a different output filename for the saved baseline implementation. This binary is a local build artifact, not part of the submission.

The BVH partitions primitive bounding-box centroids at the median along their largest extent. Leaves contain at most four primitives by default. Closest-hit traversal checks the nearer child first and prunes using the current ray bound. Large reductions in primitive intersection tests explain the speedup; exact timings depend on the machine and system load.
