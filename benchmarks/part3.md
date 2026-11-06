# Part 3: direct illumination results

Measured on this ARM64 Mac with a Release build, 12 render threads, and 480 × 360 output
(480 × 480 for `dragon`). Single-run measurements, not averaged benchmarks. Raw renderer
output is in `part3.log` beside this file.

## Renders

| Image | Command arguments | Wall clock (s) |
|---|---|---:|
| `part3_bunny_zerobounce.png` | `-s 16 -l 8 -m 0` CBbunny | 0.30 |
| `part3_bunny_hemisphere_64_32.png` | `-s 64 -l 32 -m 6 -H` CBbunny | 31.48 |
| `part3_bunny_importance_64_32.png` | `-s 64 -l 32 -m 6` CBbunny | 22.81 |
| `part3_spheres_hemisphere_64_32.png` | `-s 64 -l 32 -m 6 -H` CBspheres_lambertian | 18.58 |
| `part3_spheres_importance_64_32.png` | `-s 64 -l 32 -m 6` CBspheres_lambertian | 10.32 |
| `part3_dragon_importance_64_32.png` | `-s 64 -l 32 -m 6 -r 480 480` dragon | 11.95 |
| `part3_bunny_light_s1_l{1,4,16,64}.png` | `-s 1 -l N -m 1` CBbunny | 0.13 / 0.16 / 0.29 / 0.73 |

At Part 3 the integrator does not recurse, so `-m 6` and `-m 1` produce identical images;
only `-m 0` differs, because a depth-zero ray is allowed no bounces and shows emission alone.
The light-sample sweep therefore uses `-m 1` to state "direct lighting only" explicitly.

## Validation against the course reference images

The Fall 2026 spec (`../context/hw3_4.pdf`) embeds reference renders for two of these exact
commands. Rasterizing those PDF pages and comparing mean linear radiance over matched image
regions:

| Region | Hemisphere: mine / reference | Importance: mine / reference |
|---|---:|---:|
| back wall, upper | 0.999 | 0.969 |
| back wall, middle | 1.003 | 0.969 |
| floor, front | 1.004 | 0.973 |
| floor, middle | 1.005 | 0.976 |
| bunny body | 0.998 | 0.992 |
| left wall (20 px strip) | 1.059 | 1.021 |
| right wall (20 px strip) | 1.043 | 1.005 |

Agreement is within a few percent everywhere; the thin side-wall strips are the worst case
because the reference has been through PDF JPEG compression and resampling. Both estimators
reproduce the reference solution.

## Noise: hemisphere versus light sampling

Per-pixel residual standard deviation after removing the smooth gradient with a 5 × 5
high-pass, measured on flat regions of the two 64 spp / 32 light-sample CBbunny renders:

| Region | Hemisphere | Importance | Ratio |
|---|---:|---:|---:|
| back wall | 0.0368 | 0.0070 | 5.2× |
| floor | 0.0387 | 0.0053 | 7.4× |
| left wall | 0.0258 | 0.0022 | 11.8× |

At equal sample counts, uniform hemisphere sampling is 5–12× noisier, and it is also slower
per image (31.5 s versus 22.8 s) because every sample casts a full closest-hit ray into the
scene instead of a shadow ray that can stop at the first occluder. The gap widens as the
light subtends a smaller solid angle: most hemisphere directions miss the light entirely and
contribute nothing, while every light sample lands on the emitter by construction.

## Soft-shadow noise versus light samples

CBbunny at one camera sample per pixel, light sampling, `-m 1`. RMSE is against the converged
`part3_bunny_importance_64_32.png`; the shadow region is the floor penumbra around the bunny
(rows 288–332, columns 140–345).

| Light samples (`-l`) | RMSE, full image | RMSE, penumbra |
|---:|---:|---:|
| 1 | 0.0977 | 0.2364 |
| 4 | 0.0580 | 0.1179 |
| 16 | 0.0446 | 0.0652 |
| 64 | 0.0410 | 0.0428 |

Penumbra error roughly halves for each 4× increase in light samples, which is the expected
1/√N Monte Carlo behaviour. It flattens between 16 and 64 because at one camera sample per
pixel the remaining error is dominated by pixel-level aliasing and by residual noise in the
reference, not by light sampling.

## Two starter-code quirks worth knowing

**Framing depends on the output resolution.** `Application::load` configures the camera at the
default 800 × 600, and `-r` then calls `Camera::set_screen_size`, which holds `screenDist`
fixed and recomputes the field of view from the new pixel dimensions
(`src/pathtracer/camera.cpp:83`). Rendering at `-r 240 180` therefore zooms in rather than
producing a smaller version of the same picture. Always render deliverables at 480 × 360 (or
whatever resolution the spec names for a scene), and never compare images taken at different
resolutions region-by-region.

**`AreaLight::sample_L` returns a pdf that is off by a factor of the distance.**
`src/scene/light.cpp:91` computes

```cpp
*pdf = sqDist / (area * fabs(cosTheta));   // cosTheta = dot(d, direction), d NOT normalized
```

Since `cosTheta` here is `dist * cos(theta)`, this evaluates to `dist / (area * |cos|)`, while
the correct solid-angle density for sampling a point uniformly on the light is
`dist² / (area * |cos|)`. The estimator therefore over-weights distant points.

This was confirmed experimentally. The ground truth is a converged uniform-hemisphere render
(`-s 256 -l 32 -m 1 -H`, 8192 samples/pixel, 480 × 360), which never calls `AreaLight::sample_L`
and so is independent of the pdf under test. Against it, 64 spp / 32 light-sample light-sampling
renders built with the shipped line and with `fabs(cosTheta / dist)` substituted give:

| Region (ordered by distance from the ceiling light) | shipped / truth | patched / truth |
|---|---:|---:|
| back wall, top (nearest the light) | 1.051 | 1.184 |
| back wall, upper | 1.090 | 1.142 |
| back wall, middle | 1.205 | 1.062 |
| bunny body | 1.237 | 1.074 |
| left red wall | 1.408 | 1.009 |
| right blue wall | 1.414 | 1.013 |
| floor, middle | 1.628 | 0.983 |
| floor, front (farthest) | 1.661 | 1.003 |

The shipped build runs 5–66% hot, and the error grows monotonically with distance from the
light, exactly as a missing factor of `dist` predicts. The patched build agrees with the
unbiased estimator to within 1–2% over the walls and floor; its remaining 6–18% deviation is
confined to the band nearest the light, which is where the one-sided `AreaLight` and the
two-sided emissive mesh genuinely model different things — the "glow" difference the starter
comment in `estimate_direct_lighting_hemisphere` already warns about.

(Under 2% of pixels are saturated in any of the three images, so 8-bit clamping is not driving
these ratios.)

**The file was left unmodified anyway**, because the course's own reference images were
generated with the same shipped code: the table above shows the as-shipped build matching the
spec's `bunny_64_32.png` to within 3%, whereas the patched build does not. Changing it would
make these renders disagree with the reference solution. The consequence to keep in mind is
that the hemisphere-versus-importance comparison in the write-up legitimately shows an overall
brightness difference, and that difference comes from the provided light sampling code, not
from either estimator implementation.

Strictly speaking, then, the two estimators in this renderer do *not* converge to the same
image, even though they should. That is worth one honest sentence in the write-up rather than
being papered over.
