# How the map layers were built

Put `OSPackageProposedMasterplan.pdf` in `source/` (it is gitignored). All page coordinates are in points on sheet 1.

1. **Proposed layer.** Render the frame at 180 dpi (2.5 px/pt) in five strips and stack them:
   `pdftoppm -f 1 -l 1 -r 180 -x 75 -y $((1050 + i*2100)) -W 13925 -H 2100 -png source/OSPackageProposedMasterplan.pdf prop_$i`
2. **Today layer** (the survey base only):
   - `pdftocairo -svg -f 1 -l 1 source/OSPackageProposedMasterplan.pdf mp1.svg`
   - `python3 -I tools/extract.py mp1.svg full.json 30 420 5600 4620`
   - `python3 -I tools/today.py full.json today_hi.html 5570 4200 13925`
   - `node tools/render_today_strips.js $PWD/today_hi.html outdir`
   - Lakes: copy pixels of colour (210,244,255) from the proposed raster where page x < 600, or x < 3330 and y > 3000. Close the mask with a 13 px max/min filter and paint them (198,226,236).
3. **Clean the proposed raster.**
   - **Builder and community names:** the polygons are in `data/masked_labels.json`. Replace dark text pixels (luminance < 120) by iterative neighbour fill. On the bend bridge deck, repaint the letters in the deck grey (124,128,130).
   - **Sheet title:** white out page x 2300–4060, y 420–565.
   - **Drawing lake and zone labels** (OSMAN SAGAR, HIMAYATH SAGAR, ZONE 1 A/B): inpaint the dark pixels. The page draws its own labels.
4. **Plan layer for satellite.** Take the cleaned proposed raster and make pixels transparent where saturation < 28 and luminance > 150, plus the lake areas.
5. **Tiles:**
   - `python3 -I tools/tile_bundles.py in.png out_dir bg_r,bg_g,bg_b quality [rgba]`
   - then `python3 -I tools/bundles_to_json.py out_dir`
   - Backgrounds: proposed 255,255,255 at q80; today 247,245,239 at q78; plan rgba at q82.

**Positions:**
- Stops and features come from chainage label positions (`data/chainage_pts.json`) and the bridge and dam chainages in the design reports. See `tools/build_v2_data.py`.
- Bridge chainages are in the DBR, Roads and Bridges, Tables 2-2 and 2-3.
- Rubber dam chainages are in the DBR, Rubber Dams (Zones A and B).
