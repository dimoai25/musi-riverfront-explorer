#!/bin/sh
# Fit the georeference from data/control_points.csv and rebuild the MapLibre tiles in site/xyz/.
# Run from the repo root once the control points have real lat/lng:  sh tools/make_xyz.sh
# Check the printed RMS and the per-point errors before committing; a point whose
# left-out error is far above the rest is probably mis-clicked.
set -e
python3 -I tools/georef.py data/control_points.csv data/georef.json
cp data/georef.json site/georef.json
python3 -I tools/warp_tiles.py data/georef.json site/tiles/proposed site/xyz/proposed --bg 255,255,255 --q 80
python3 -I tools/warp_tiles.py data/georef.json site/tiles/today site/xyz/today --bg 247,245,239 --q 78
python3 -I tools/warp_tiles.py data/georef.json site/tiles/plan site/xyz/plan --q 82
