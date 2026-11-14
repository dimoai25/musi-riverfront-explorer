"""Georeference the pilot window (drawing points) to WGS84 from control points.

Usage:
  python3 -I georef.py data/control_points.csv data/explorer_stops_features.json out_dir/

control_points.csv columns: id,x_pt,y_pt,lat,lng,note
  x_pt, y_pt are window coordinates (origin top-left of the pilot window, y down),
  the same frame as data/explorer_stops_features.json. Rows with blank lat/lng are skipped.

Writes to out_dir/:
  georef.json          fitted transform, residuals per point, RMS (m), implied scale and rotation,
                       window corner lat/lngs (for a rotated image overlay)
  stops.geojson        stop pins (Point) and stop boxes (Polygon)
  features.geojson     bridges, nodes, parks, dams, places, chainage anchors (Point)
  gdal_commands.sh     gdal_translate/gdalwarp/gdal2tiles commands with GCPs for the rasters

Method: project lat/lng to a local tangent plane (equirectangular about the mean latitude; error
is negligible over a 5 km window), least-squares fit pt -> metres (similarity for 2 points,
affine for 3 or more), then invert back to lat/lng. No third-party dependencies.
"""
import csv, json, math, os, sys

R = 6371008.8
PX_PER_PT = 2.5  # pilot rasters: 5475 x 2850 px for 2190 x 1140 pt
W_PT, H_PT = 2190, 1140


def load_points(path):
    pts = []
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            if not (r.get('lat') or '').strip() or not (r.get('lng') or '').strip():
                continue
            pts.append({'id': r['id'], 'x': float(r['x_pt']), 'y': float(r['y_pt']),
                        'lat': float(r['lat']), 'lng': float(r['lng']), 'note': r.get('note', '')})
    return pts


def solve(A, b):
    """Least squares via normal equations (small systems only)."""
    n = len(A[0])
    M = [[sum(A[k][i] * A[k][j] for k in range(len(A))) for j in range(n)] for i in range(n)]
    v = [sum(A[k][i] * b[k] for k in range(len(A))) for i in range(n)]
    for c in range(n):  # Gauss-Jordan with partial pivoting
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]; v[c], v[p] = v[p], v[c]
        if abs(M[c][c]) < 1e-12:
            raise SystemExit('Control points are degenerate (collinear or duplicated).')
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [M[r][j] - f * M[c][j] for j in range(n)]
                v[r] -= f * v[c]
    return [v[i] / M[i][i] for i in range(n)]


def main():
    cp_path, feat_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    pts = load_points(cp_path)
    if len(pts) < 2:
        raise SystemExit(f'Need at least 2 control points with lat/lng; found {len(pts)}.')
    lat0 = sum(p['lat'] for p in pts) / len(pts)
    lng0 = sum(p['lng'] for p in pts) / len(pts)
    kx = R * math.cos(math.radians(lat0)) * math.pi / 180
    ky = R * math.pi / 180
    for p in pts:
        p['E'] = (p['lng'] - lng0) * kx
        p['N'] = (p['lat'] - lat0) * ky

    if len(pts) == 2:  # similarity: E = a x - b y + c ; N = -(b x + a y) + d  (y down)
        A, rhs = [], []
        for p in pts:
            A.append([p['x'], -p['y'], 1, 0]); rhs.append(p['E'])
            A.append([-p['y'], -p['x'], 0, 1]); rhs.append(p['N'])
        a, b, c, d = solve(A, rhs)
        T = [a, -b, c, -b, -a, d]
        model = 'similarity'
    else:  # affine: E = t0 x + t1 y + t2 ; N = t3 x + t4 y + t5
        A = [[p['x'], p['y'], 1] for p in pts]
        e = solve(A, [p['E'] for p in pts]); n = solve(A, [p['N'] for p in pts])
        T = e + n
        model = 'affine'

    def fwd(x, y):
        E = T[0] * x + T[1] * y + T[2]
        N = T[3] * x + T[4] * y + T[5]
        return lat0 + N / ky, lng0 + E / kx

    res = []
    for p in pts:
        E = T[0] * p['x'] + T[1] * p['y'] + T[2]
        N = T[3] * p['x'] + T[4] * p['y'] + T[5]
        res.append({'id': p['id'], 'residual_m': round(math.hypot(E - p['E'], N - p['N']), 1)})
    rms = math.sqrt(sum(r['residual_m'] ** 2 for r in res) / len(res))
    sx = math.hypot(T[0], T[3]); sy = math.hypot(T[1], T[4])
    rot = math.degrees(math.atan2(T[3], T[0]))  # rotation of drawing x-axis from east, CCW positive

    corners = {k: fwd(x, y) for k, (x, y) in
               {'top_left': (0, 0), 'top_right': (W_PT, 0), 'bottom_right': (W_PT, H_PT), 'bottom_left': (0, H_PT)}.items()}
    lats = [c[0] for c in corners.values()]; lngs = [c[1] for c in corners.values()]
    geo = {
        'model': model, 'n_points': len(pts), 'origin_lat_lng': [lat0, lng0],
        'coeffs_pt_to_local_m': T, 'local_m_per_deg': [kx, ky],
        'implied_m_per_pt': [round(sx, 4), round(sy, 4)], 'expected_m_per_pt': 2.1,
        'drawing_rotation_deg_ccw_from_east': round(rot, 3),
        'residuals': res, 'rms_m': round(rms, 1),
        'window_corners_lat_lng': corners,
        'north_up_bounds': {'south': min(lats), 'west': min(lngs), 'north': max(lats), 'east': max(lngs)},
        'note': 'Residuals are 0 with 2-3 points (exact fit); use 4+ points for a meaningful RMS.',
    }
    json.dump(geo, open(os.path.join(out, 'georef.json'), 'w'), indent=1)

    D = json.load(open(feat_path))
    sf = []
    for s in D['stops']:
        props = {k: s.get(k) for k in ('id', 'n', 'short', 'name', 'ch')}
        if s.get('pin'):
            la, ln = fwd(*s['pin'])
            sf.append({'type': 'Feature', 'properties': dict(props, kind='stop_pin'),
                       'geometry': {'type': 'Point', 'coordinates': [round(ln, 7), round(la, 7)]}})
        if s.get('box'):
            x0, y0, x1, y1 = s['box']
            ring = [fwd(x, y) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))]
            sf.append({'type': 'Feature', 'properties': dict(props, kind='stop_box'),
                       'geometry': {'type': 'Polygon', 'coordinates': [[[round(b, 7), round(a, 7)] for a, b in ring]]}})
    json.dump({'type': 'FeatureCollection', 'features': sf}, open(os.path.join(out, 'stops.geojson'), 'w'))

    ff = []
    for f in D['features']:
        if 'x' not in f:
            continue
        la, ln = fwd(f['x'], f['y'])
        ff.append({'type': 'Feature', 'properties': {k: v for k, v in f.items() if k not in ('x', 'y')},
                   'geometry': {'type': 'Point', 'coordinates': [round(ln, 7), round(la, 7)]}})
    json.dump({'type': 'FeatureCollection', 'features': ff}, open(os.path.join(out, 'features.geojson'), 'w'))

    g = ' '.join(f'-gcp {p["x"] * PX_PER_PT:.1f} {p["y"] * PX_PER_PT:.1f} {p["lng"]:.7f} {p["lat"]:.7f}' for p in pts)
    order = '-order 1' if len(pts) >= 3 else ''
    with open(os.path.join(out, 'gdal_commands.sh'), 'w') as f:
        f.write('#!/bin/sh\n# Warp the pilot rasters (5475x2850 px) to Web Mercator and cut XYZ tiles.\nset -e\n')
        for name in ('proposed', 'today'):
            f.write(f'gdal_translate -of GTiff -a_srs EPSG:4326 {g} assets/{name}_full.png /tmp/{name}_gcp.tif\n')
            f.write(f'gdalwarp -overwrite {order} -r bilinear -t_srs EPSG:3857 -dstalpha /tmp/{name}_gcp.tif build/{name}_3857.tif\n')
            f.write(f'gdal2tiles.py --xyz -z 13-19 -w none build/{name}_3857.tif public/tiles/{name}\n')
    print(json.dumps({k: geo[k] for k in ('model', 'n_points', 'rms_m', 'implied_m_per_pt', 'drawing_rotation_deg_ccw_from_east')}))


if __name__ == '__main__':
    main()
