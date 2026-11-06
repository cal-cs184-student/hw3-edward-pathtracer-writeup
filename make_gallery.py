#!/usr/bin/env python3
"""Builds docs/render_gallery.html, a contact sheet of every saved render.

This is a review aid for checking results at a glance, not the submitted
write-up. Re-run it after any render campaign finishes:

    python3 docs/make_gallery.py
"""
import html
import os

IMG_DIR = os.path.join(os.path.dirname(__file__), "images")
OUT = os.path.join(os.path.dirname(__file__), "render_gallery.html")

# (filename, caption, command-tail). Sections are rendered in this order.
SECTIONS = [
    ("part5", "Part 5 — Adaptive Sampling",
     "Samples concentrated where the image is still noisy. In the rate images "
     "blue is a pixel that converged early, red one that spent its whole budget.", [
        ("pair", "CBbunny — 2048 max samples, 1 light ray, depth 5", [
            ("part5_bunny_adaptive.png", "Rendered result", "-s 2048 -a 64 0.05 -l 1 -m 5"),
            ("part5_bunny_adaptive_rate.png", "Sampling rate", "696 avg samples/px"),
        ]),
        ("pair", "CBspheres_lambertian — 2048 max samples, 1 light ray, depth 5", [
            ("part5_spheres_adaptive.png", "Rendered result", "-s 2048 -a 64 0.05 -l 1 -m 5"),
            ("part5_spheres_adaptive_rate.png", "Sampling rate", "850 avg samples/px"),
        ]),
        ("pair", "The same budget without adaptive sampling", [
            ("part5_bunny_fixed2048.png", "Fixed 2048 samples", "-s 2048 -l 1 -m 5"),
            ("part5_bunny_adaptive.png", "Adaptive, same budget", "-s 2048 -a 64 0.05"),
        ]),
    ]),
    ("part4", "Part 4 — Global Illumination", "Indirect light: every bounce past the first.", [
        ("series", "Global illumination at 1024 samples/pixel", [
            ("part4_gi_bunny_1024.png", "CBbunny", "-s 1024 -l 4 -m 5"),
            ("part4_gi_spheres_1024.png", "CBspheres_lambertian", "-s 1024 -l 4 -m 5"),
            ("part4_gi_dragon_1024.png", "dragon", "-s 1024 -l 4 -m 5 -r 480 480"),
        ]),
        ("pair", "Direct versus indirect illumination", [
            ("part4_bunny_direct_1024.png", "Direct only", "-m 1 -o 1"),
            ("part4_bunny_indirect_1024.png", "Indirect only", "-m 5 -o 1 -I"),
        ]),
        ("strip", "Isolated bounces — the m-th bounce alone", [
            ("part4_bunny_isolated_m%d_1024.png" % m, "m = %d" % m, "-m %d -o 0 -R 0" % m)
            for m in range(6)
        ]),
        ("strip", "Accumulated bounces — every bounce up to m", [
            ("part4_bunny_accum_m%d_1024.png" % m, "m = %d" % m, "-m %d -o 1 -R 0" % m)
            for m in range(6)
        ]),
        ("strip", "Russian roulette termination", [
            ("part4_bunny_rr_m%s_1024.png" % m, "m = %s" % m, "-m %s -o 1 -R 1" % m)
            for m in ["0", "1", "2", "3", "4", "100"]
        ]),
        ("strip", "Samples per pixel, four light rays", [
            ("part4_bunny_spp%s_l4.png" % s, "%s spp" % s, "-s %s -l 4 -m 5" % s)
            for s in ["1", "2", "4", "8", "16", "64", "1024"]
        ]),
    ]),
    ("part3", "Part 3 — Direct Illumination", "One bounce of light, two ways to estimate it.", [
        ("pair", "CBbunny — 64 spp, 32 light rays", [
            ("part3_bunny_hemisphere_64_32.png", "Uniform hemisphere", "-s 64 -l 32 -m 6 -H"),
            ("part3_bunny_importance_64_32.png", "Light sampling", "-s 64 -l 32 -m 6"),
        ]),
        ("pair", "CBspheres_lambertian — 64 spp, 32 light rays", [
            ("part3_spheres_hemisphere_64_32.png", "Uniform hemisphere", "-s 64 -l 32 -m 6 -H"),
            ("part3_spheres_importance_64_32.png", "Light sampling", "-s 64 -l 32 -m 6"),
        ]),
        ("strip", "Soft-shadow noise versus light rays, one camera sample", [
            ("part3_bunny_light_s1_l%s.png" % l, "%s light ray%s" % (l, "" if l == "1" else "s"),
             "-s 1 -l %s -m 1" % l)
            for l in ["1", "4", "16", "64"]
        ]),
        ("series", "Other direct-lighting renders", [
            ("part3_dragon_importance_64_32.png", "dragon", "-s 64 -l 32 -m 6 -r 480 480"),
            ("part3_bunny_zerobounce.png", "Zero bounce only", "-s 16 -l 8 -m 0"),
        ]),
    ]),
    ("part2", "Part 2 — Bounding Volume Hierarchy", "Normal shading on scenes too large to brute force.", [
        ("series", "BVH-accelerated renders", [
            ("part2_cow.png", "cow — 5,856 primitives", "75.2x speedup"),
            ("part2_beetle.png", "beetle — 7,558 primitives", "77.1x speedup"),
            ("part2_banana.png", "banana — 2,458 primitives", "24.2x speedup"),
            ("part2_maxplanck.png", "maxplanck — 50,801 primitives", "0.0435 s render"),
            ("part2_lucy.png", "CBlucy — 133,796 primitives", "0.0595 s render"),
        ]),
    ]),
    ("part1", "Part 1 — Ray Generation and Intersection", "Camera rays, triangles, spheres, normal shading.", [
        ("series", "First renders", [
            ("part1_empty.png", "CBempty", "-s 4 -t 1"),
            ("part1_spheres.png", "CBspheres_lambertian", "-s 4 -t 1"),
            ("part1_banana.png", "banana", "-s 4 -t 1"),
        ]),
    ]),
]

CSS = """
:root {
  color-scheme: light dark;
  --void: #0B0B0E;
  --well: #0B0B0E;
  --page: #F7F5F1;
  --panel: #FFFFFF;
  --rule: #DDD8CF;
  --ink: #1C1A17;
  --ink-soft: #6A6459;
  --accent: #9A7B22;
  --red: #B2524F;
  --blue: #5B5BA8;
  --mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --page: #0E0E12;
    --panel: #15151A;
    --rule: #2A2A32;
    --ink: #E8E6E1;
    --ink-soft: #908A7E;
    --accent: #F5E9C8;
  }
}
:root[data-theme="dark"] {
  --page: #0E0E12;
  --panel: #15151A;
  --rule: #2A2A32;
  --ink: #E8E6E1;
  --ink-soft: #908A7E;
  --accent: #F5E9C8;
}
:root[data-theme="light"] {
  --page: #F7F5F1;
  --panel: #FFFFFF;
  --rule: #DDD8CF;
  --ink: #1C1A17;
  --ink-soft: #6A6459;
  --accent: #9A7B22;
}

body {
  margin: 0;
  background: var(--page);
  color: var(--ink);
  font-family: var(--sans);
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 1180px; margin: 0 auto; padding: 0 24px 96px; }

header.masthead {
  padding: 72px 0 36px;
  border-bottom: 1px solid var(--rule);
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.eyebrow {
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-soft);
}
h1 {
  font-family: var(--mono);
  font-size: clamp(26px, 4vw, 40px);
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0;
  text-wrap: balance;
}
.lede { margin: 0; max-width: 62ch; color: var(--ink-soft); font-size: 16px; }

nav.jump {
  position: sticky; top: 0; z-index: 10;
  display: flex; flex-wrap: wrap; gap: 6px;
  padding: 12px 0;
  background: color-mix(in srgb, var(--page) 92%, transparent);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--rule);
  margin-bottom: 8px;
}
nav.jump a {
  font-family: var(--mono); font-size: 12px; letter-spacing: 0.04em;
  color: var(--ink-soft); text-decoration: none;
  padding: 6px 11px; border: 1px solid var(--rule); border-radius: 2px;
}
nav.jump a:hover, nav.jump a:focus-visible { color: var(--ink); border-color: var(--ink-soft); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

section.part { padding-top: 56px; }
.part-head { display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; }
h2 {
  font-family: var(--mono); font-size: 20px; font-weight: 600;
  letter-spacing: -0.01em; margin: 0;
}
.part-note { margin: 0; color: var(--ink-soft); font-size: 14px; }

h3 {
  font-family: var(--mono);
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--ink-soft);
  margin: 40px 0 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--rule);
}

.grid { display: grid; gap: 18px; }
.grid.pair   { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
.grid.series { grid-template-columns: repeat(auto-fill, minmax(268px, 1fr)); }
.grid.strip  { grid-template-columns: repeat(auto-fill, minmax(212px, 1fr)); }

figure { margin: 0; display: flex; flex-direction: column; gap: 9px; }
.well {
  display: block;
  background: var(--well);
  border: 1px solid var(--rule);
  line-height: 0;
  overflow: hidden;
}
.well img { width: 100%; height: auto; display: block; }
.well:hover { border-color: var(--accent); }
figcaption { display: flex; flex-direction: column; gap: 3px; }
.cap-name { font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; }
.cap-cmd {
  font-family: var(--mono); font-size: 11px; color: var(--ink-soft);
  font-variant-numeric: tabular-nums; word-break: break-word;
}

.pending {
  display: flex; align-items: center; justify-content: center;
  aspect-ratio: 4 / 3; background: var(--panel);
  border: 1px dashed var(--rule);
  font-family: var(--mono); font-size: 11px; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink-soft);
}

footer {
  margin-top: 72px; padding-top: 20px;
  border-top: 1px solid var(--rule);
  font-family: var(--mono); font-size: 11px; color: var(--ink-soft);
}
"""


def figure_html(fname, name, cmd):
    path = os.path.join(IMG_DIR, fname)
    name_e, cmd_e, f_e = html.escape(name), html.escape(cmd), html.escape(fname)
    if not os.path.exists(path):
        body = '<div class="pending">rendering</div>'
    else:
        body = ('<a class="well" href="%s" target="_blank" rel="noopener">'
                '<img src="%s" alt="%s" loading="lazy"></a>' % (f_e, f_e, name_e))
    return ('<figure>%s<figcaption><span class="cap-name">%s</span>'
            '<span class="cap-cmd">%s</span></figcaption></figure>'
            % (body, name_e, cmd_e))


def build():
    present = sum(
        1 for _, _, _, groups in SECTIONS for _, _, items in groups
        for f, _, _ in items if os.path.exists(os.path.join(IMG_DIR, f))
    )
    total = sum(len(items) for _, _, _, groups in SECTIONS for _, _, items in groups)

    nav = "".join('<a href="#%s">%s</a>' % (sid, html.escape(title.split(" — ")[0]))
                  for sid, title, _, _ in SECTIONS)

    parts = []
    for sid, title, note, groups in SECTIONS:
        blocks = []
        for kind, heading, items in groups:
            figs = "".join(figure_html(*it) for it in items)
            blocks.append('<h3>%s</h3><div class="grid %s">%s</div>'
                          % (html.escape(heading), kind, figs))
        parts.append(
            '<section class="part" id="%s"><div class="part-head"><h2>%s</h2>'
            '<p class="part-note">%s</p></div>%s</section>'
            % (sid, html.escape(title), html.escape(note), "".join(blocks)))

    page = """<title>CS 184 Homework 3 — Render Contact Sheet</title>
<style>%s</style>
<div class="wrap">
<header class="masthead">
  <span class="eyebrow">CS 184/284A · Homework 3 · Path Tracer</span>
  <h1>Render contact sheet</h1>
  <p class="lede">Every image saved by the renderer so far, grouped by the comparison it is
  meant to support. Click any frame to open it at full size. Frames marked
  <em>rendering</em> are still queued.</p>
</header>
<nav class="jump">%s</nav>
%s
<footer>%d of %d renders saved · 480 &times; 360 unless noted · generated by docs/make_gallery.py</footer>
</div>
""" % (CSS, nav, "".join(parts), present, total)

    with open(OUT, "w") as fh:
        fh.write(page)
    print("wrote %s (%d/%d renders present)" % (OUT, present, total))


if __name__ == "__main__":
    build()
