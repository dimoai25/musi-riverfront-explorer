# Musi Riverfront Explorer: notes for anyone working in this repo

A public, phone-first explorer of the Musi Riverfront Development Project (Hyderabad, Phase 1, Zones 1A and 1B), read from the public tender drawings. It is made by @Vamsidhar_t and shared on X. The audience is homeowners, home buyers, builders and investors. Most visitors arrive from X or WhatsApp on a phone.

The live site is `site/`, deployed to GitHub Pages by `.github/workflows/pages.yml` on every push to `main`. Its URL is https://dimoai25.github.io/musi-riverfront-explorer/.

## Guardrails (do not break)
- **Permanent note on the map.** It must always be visible: "Approximate overlay based on public plans. Not for judging impact on any specific property or land acquisition."
- **No builder or project names**, on the map, in the copy, or anywhere in this repo (it is public). Gated-community names printed on the drawing have been removed from the plan image, the text and the committed data. The design reports name some bridges after them; we use neutral names instead (bend bridge, Ibrahimbagh bridge, Goshala bridge). `tools/build_v2_data.py` refuses output containing them, checked by hashed word so the names never appear in code.
- **No completion dates or timelines.** The drawing revision line ("Rev R02, Sep 2026") is fine.
- **List the source document for each stretch.** This is in `data/data.json` → `SOURCES`, shown in each stretch intro and in the Documents tab.
- **Interpretations say "my reading".** Footbridges are flagged "not included in DPR".
- **Never invent coordinates, projects, prices or traffic numbers.** Leave a stretch out rather than guess.
- **Don't republish the tender PDFs here.** Link to the official portal instead.

## Status (15 Nov 2026)
- **v2 is live:**
  - Zone 1B: Osman Sagar → Bapu Ghat, Ch 0+600 → 12+212, including the Tipu Khan bridge (Ch 10+800).
  - Zone 1A: Himayat Sagar → Bapu Ghat, Ch 1+200 → 9+140, including the Rajendranagar Road / Agriculture University nala area.
  - Today / Compare / Proposed swipe, stretch switcher, 16 stops, sources per stretch.
- **Satellite is coded but off.** It switches on when `site/config.json` exists with imagery and a georeference (see below).
- **Next: rebuild on MapLibre GL** in real coordinates, on a branch. That gives smoother zoom and pan, standard tiles, and satellite with the plan on top. Ship it once georeferencing is done.

## MapLibre version (branch `maplibre`)
- **Same page, new map engine.** `app/body.html` keeps the v2 panel, tour, stretches and markers. The map is MapLibre GL JS 5.6.0, self-hosted in `site/vendor/` (npm and the CDNs are blocked from the build sandbox; the release zip comes from GitHub).
- **Two synced maps:**
  - `mapA` (underneath) shows today, or satellite.
  - `mapB` (on top) shows proposed, or the plan over satellite. It takes the gestures and holds the markers.
  - Compare clips only mapB's canvas, so the markers stay whole.
- **Runtime files in `site/`:**
  - `georef.json` (the fit output) is required; without it the map shows a "could not load" note.
  - `xyz/{today,proposed,plan}/{z}/{x}/{y}.webp` are the tiles, z11 to z17, with `tiles.json`.
  - `config.json` is optional and holds only the satellite URL and attribution.
- **Build the tiles:** `sh tools/make_xyz.sh`. It runs `tools/georef.py` (fit, RMS and leave-one-out errors per point), then `tools/warp_tiles.py` per layer. The warper reads the v2 bundles in `site/tiles/`, so the repo alone is enough. It takes about 7 minutes per layer.
- **Never commit a made-up georef.** Testing uses synthetic points in the scratchpad only.

## Coordinate frame
- **Source:** master plan sheet 1, drawing MHT-MP-PP-01-Z1, Rev R02, Sep 2026 (`OSPackageProposedMasterplan.pdf`, page 1). Its page is 6741 × 4768 pt, rendered landscape.
- **Frame:**
  - frame point = page point − (30, 420), size 5570 × 4200 pt
  - raster scale 2.5 px/pt, giving a native raster of 13925 × 10500 px
  - ground scale about 2.1 m per point (about 0.84 m per pixel)
- **Legacy v1 "window" coordinates:** frame = window + (440, 260).
- **Chainage positions:**
  - `data/chainage_pts.json` holds chainage label positions (page pt) per zone, from `pdftotext -bbox`.
  - `data/placed.json` holds the bridges and rubber dams placed by chainage.
- **Control points:** `data/control_points.csv`, ten existing road/river features in page pt. The guide is `docs/control_points_10.png`. Lat/lng are being captured by the owner from Google Maps.

## Satellite config (`site/config.json`, not committed until the coordinates are real)
```json
{"satellite": {"url": "https://…/{z}/{y}/{x}?token=KEY", "attribution": "…", "maxZoom": 19},
 "georef": {"lat0": 0, "lng0": 0, "kx": 0, "ky": 0, "T": [a, b, c, d, e, f]}}
```
- `T` maps **frame points** to local metres: E = a·x + b·y + c, N = d·x + e·y + f.
- `lat = lat0 + N/ky`, `lng = lng0 + E/kx`, with `kx = R·cos(lat0)·π/180` and `ky = R·π/180`.
- Fit `T` by least squares from the control points (`tools/georef_v1_window.py` shows the method; convert page → frame first). Report the RMS in metres and check each residual.
- **Imagery provider:** Esri's keyless basemaps are deprecated. Use a key (ArcGIS Location Platform or similar) restricted by HTTP referrer to the Pages domain. The key is visible in client code by design; the referrer restriction is the protection.

## Layout
- `site/`: the deployed static site.
  - `index.html` holds all CSS, JS and data inline.
  - `tiles/{today,proposed,plan}/` holds 256 px WebP tiles in 8×8 JSON bundles (`z{z}_{bx}_{by}.json` = {"x_y": base64 webp}, plus `meta.json`).
  - `plan` is the transparent plan used over satellite.
- `app/`: page source (`base.css`, `extra.css`, `body.html` with a `/*DATA*/` placeholder).
- `data/`: `data.json` (STOPS, FEATURES, DOCS, STRETCHES, SOURCES), chainage data, labels, masked-label polygons, control points.
- `tools/`: the pipeline (see `docs/build.md`).
- `private/` (gitignored, local only, may be absent in a fresh clone): the internal knowledge base (project facts, tender review, feasibility research) and the unredacted source data. Never commit it; the repo is public.

## Rebuild the page
```sh
python3 -I tools/build_v2_data.py data/v1data.json data/placed.json data/data.json
python3 -I tools/build_v2_page.py app data/data.json /tmp/artifact.html site/index.html https://dimoai25.github.io/musi-riverfront-explorer/
```
Rebuilding the rasters and tiles needs the tender PDFs in `source/` (gitignored); see `docs/build.md`.
