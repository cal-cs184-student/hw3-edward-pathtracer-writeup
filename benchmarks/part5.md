# Part 5: adaptive sampling results

Measured on this ARM64 Mac with a Release build, 12 render threads, 480 × 360 output,
one light ray and max ray depth 5. Single-run measurements. Raw renderer output is in
`part5.log`; `render_part5.sh` regenerates every image.

## How the early exit is wired

`-a <batch> <tolerance>` is what *enables* adaptive sampling, matching the spec's wording
that "once the `-a` argument is specified, the previous sampling rate assigned by argument
`-s` now represents the maximum number of samples". This matters: the starter already
defaults `samplesPerBatch` to 32 and `maxTolerance` to 0.05, so an implementation that keys
off those values alone would adapt on *every* render and silently invalidate every fixed
sample-count image from Parts 1 through 4. `PathTracer::use_adaptive_sampling` defaults to
false and only `-a` turns it on.

Verified directly: rendering without `-a` produces a `_rate.png` containing exactly one
distinct colour, meaning every pixel took the full `ns_aa` samples.

## Renders

| Image | Command arguments | Wall clock (s) |
|---|---|---:|
| `part5_bunny_adaptive.png` | `-s 2048 -a 64 0.05 -l 1 -m 5` CBbunny | 47.12 |
| `part5_spheres_adaptive.png` | `-s 2048 -a 64 0.05 -l 1 -m 5` CBspheres_lambertian | 28.17 |
| `part5_bunny_fixed2048.png` | `-s 2048 -l 1 -m 5` CBbunny (no adaptation) | 138.33 |

Each adaptive render also writes a `_rate.png` beside it.

## What the early exit buys

CBbunny at the same 2048-sample budget, with and without adaptation:

| | Wall clock | Avg samples/pixel |
|---|---:|---:|
| Fixed | 138.33 s | 2048 |
| Adaptive | 47.12 s | 696 |
| **Ratio** | **2.94×** | **2.94×** |

The two ratios agreeing to three significant figures is the useful result: the time saved is
exactly proportional to the samples skipped, so testing convergence once per 64-sample batch
costs nothing measurable.

The two images are the same picture — mean linear radiance differs by 0.03% and the RMSE
between them is 0.011 on a 0–1 scale, which is the residual Monte Carlo noise rather than any
systematic difference. Adaptive sampling is not trading quality for speed here; it is
declining to oversample pixels that had already converged.

## Where the samples actually went

The renderer's rate image maps the ratio of actual to maximum samples onto a linear
blue → green → red ramp (`raytraced_renderer.cpp:737`), so it inverts exactly: a pixel's
rate is `0.5 * (1 - B)` on the blue half of the ramp and `1 - 0.5 * G` on the red half.
Decoding the saved images gives the real distribution of effort.

| Scene | Mean rate | Avg samples/pixel of 2048 | Pixels under 10% of budget | Pixels over 90% |
|---|---:|---:|---:|---:|
| CBbunny | 0.340 | 696 | 26.6% | 13.1% |
| CBspheres_lambertian | 0.415 | 850 | 17.5% | 18.3% |

So the bunny render reaches a noise-free result while tracing about one third of the rays a
uniform 2048-sample pass would need.

## Reading the rate images

The structure is the same in both scenes and follows directly from where variance lives:

- **Blue, converged almost immediately.** The flat, directly-lit back wall; the open floor
  away from any object; the area light itself, whose radiance is constant so its variance is
  exactly zero; and the black surround outside the box, where every sample returns zero and
  the convergence test reduces to `0 <= 0`.
- **Red, spent the whole budget.** Contact shadows under the bunny and the spheres, the
  bunny's shadowed creases, and the terminator line where each sphere curves away from the
  light. These are the regions whose illumination arrives mostly through indirect paths or
  through a partially occluded light, so each sample differs a lot from the last.
- **Green, intermediate.** The ceiling and the wall-to-wall corners. The ceiling receives no
  direct light at all — it is lit purely by bounces — which is exactly why it costs more than
  the directly-lit wall below it.

That pattern is the argument for adaptive sampling in one picture: the expensive pixels are a
minority, and a uniform sample count spends most of its effort on the pixels that were
already finished.

## Implementation notes

- Running sums `s1` of illuminance and `s2` of squared illuminance are the only state kept;
  no per-sample history is retained.
- Variance is `(s2 - s1²/n) / (n - 1)`, clamped at zero. For a pixel whose samples are all
  but identical, rounding can drive that expression slightly negative, which would make the
  following square root produce NaN and poison the pixel.
- The test is `1.96 * sqrt(variance / n) <= maxTolerance * mean`, evaluated only on batch
  boundaries and never before `n = 2`, since the `n - 1` divisor is zero at one sample.
- The pixel is averaged over the samples *actually taken*, not over `ns_aa`. Dividing by
  `ns_aa` is the natural mistake here and it darkens every converged pixel in proportion to
  how early it stopped — a bug that looks like a lighting error rather than a sampling one.
  `tests/part5_tests.cpp` pins this with a zero-variance pixel whose colour must survive
  convergence exactly.
- `sampleCountBuffer` receives the actual count so the rate image is meaningful.
