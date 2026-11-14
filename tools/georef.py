"""Fit the master-plan frame to real-world coordinates from control points.

Usage:
  python3 -I tools/georef.py data/control_points.csv data/georef.json

control_points.csv columns: id,page_x,page_y,lat,lng,description
  page_x, page_y are points on master plan sheet 1 (y down). Rows with blank lat/lng are skipped.

The frame is page minus (30, 420), 5570 x 4200 pt. The fit maps frame points to local metres
(equirectangular about the mean control latitude, error is negligible over ~12 km):
  E = a*x + b*y + c,  N = d*x + e*y + f
  lat = lat0 + N/ky,  lng = lng0 + E/kx,  ky = R*pi/180,  kx = ky*cos(lat0)

Writes georef.json with the transform, its inverse, per-point residuals, leave-one-out residuals
(a point that only fits when it is in the fit is probably mis-clicked), RMS in metres, the implied
scale and rotation, and the frame corners as [lng, lat] (TL, TR, BR, BL).
No third-party dependencies.
"""
import csv, json, math, sys

R = 6371008.8
OX, OY = 30, 420
FW, FH = 5570, 4200


def load(path):
    pts = []
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            lat, lng = (r.get('lat') or '').strip(), (r.get('lng') or '').strip()
            if not lat or not lng:
                continue
            pts.append({'id': r['id'], 'x': float(r['page_x']) - OX, 'y': float(r['page_y']) - OY,
                        'lat': float(lat), 'lng': float(lng), 'desc': r.get('description', '')})
    return pts


def lstsq(A, b):
    n = len(A[0])
    M = [[sum(A[k][i] * A[k][j] for k in range(len(A))) for j in range(n)] for i in range(n)]
    v = [sum(A[k][i] * b[k] for k in range(len(A))) for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]; v[c], v[p] = v[p], v[c]
        if abs(M[c][c]) < 1e-9:
            raise SystemExit('Control points are degenerate (collinear or duplicated).')
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [M[r][j] - f * M[c][j] for j in range(n)]
                v[r] -= f * v[c]
    return [v[i] / M[i][i] for i in range(n)]


def fit(pts, lat0, lng0):
    ky = R * math.pi / 180; kx = ky * math.cos(math.radians(lat0))
    E = [(p['lng'] - lng0) * kx for p in pts]; N = [(p['lat'] - lat0) * ky for p in pts]
    if len(pts) >= 3:
        A = [[p['x'], p['y'], 1] for p in pts]
        a, b, c = lstsq(A, E); d, e, f = lstsq(A, N)
    else:  # similarity from 2 points; note y is down on the page, N is up
        A, B = [], []
        for p, ee, nn in zip(pts, E, N):
            A += [[p['x'], p['y'], 1, 0], [-p['y'], p['x'], 0, 1]]; B += [ee, -nn]
        s, t, tx, ty = lstsq(A, B)
        a, b, c, d, e, f = s, t, tx, t, -s, -ty
    return [a, b, c, d, e, f], kx, ky


def apply(T, x, y):
    return T[0] * x + T[1] * y + T[2], T[3] * x + T[4] * y + T[5]


def invert(T):
    a, b, c, d, e, f = T
    det = a * e - b * d
    ia, ib, id_, ie = e / det, -b / det, -d / det, a / det
    return [ia, ib, -(ia * c + ib * f), id_, ie, -(id_ * c + ie * f)]


def main():
    pts = load(sys.argv[1])
    if len(pts) < 2:
        raise SystemExit(f'Need at least 2 control points with lat/lng, found {len(pts)}.')
    lat0 = sum(p['lat'] for p in pts) / len(pts); lng0 = sum(p['lng'] for p in pts) / len(pts)
    T, kx, ky = fit(pts, lat0, lng0)
    res = []
    for p in pts:
        e, n = apply(T, p['x'], p['y'])
        de, dn = e - (p['lng'] - lng0) * kx, n - (p['lat'] - lat0) * ky
        r = {'id': p['id'], 'dE_m': round(de, 1), 'dN_m': round(dn, 1), 'err_m': round(math.hypot(de, dn), 1)}
        if len(pts) >= 5:  # leave one out
            T1, _, _ = fit([q for q in pts if q is not p], lat0, lng0)
            e1, n1 = apply(T1, p['x'], p['y'])
            r['loo_err_m'] = round(math.hypot(e1 - (p['lng'] - lng0) * kx, n1 - (p['lat'] - lat0) * ky), 1)
        res.append(r)
    rms = math.sqrt(sum(r['err_m'] ** 2 for r in res) / len(res))
    sx, sy = math.hypot(T[0], T[3]), math.hypot(T[1], T[4])
    rot = math.degrees(math.atan2(T[3], T[0]))  # angle of the frame x axis, anticlockwise from east
    corners = []
    for x, y in ((0, 0), (FW, 0), (FW, FH), (0, FH)):
        e, n = apply(T, x, y)
        corners.append([round(lng0 + e / kx, 7), round(lat0 + n / ky, 7)])
    out = {'lat0': lat0, 'lng0': lng0, 'kx': kx, 'ky': ky, 'T': T, 'Tinv': invert(T),
           'frame': {'origin_page_pt': [OX, OY], 'size_pt': [FW, FH]},
           'n_points': len(pts), 'model': 'affine' if len(pts) >= 3 else 'similarity',
           'rms_m': round(rms, 1), 'scale_m_per_pt': [round(sx, 3), round(sy, 3)],
           'rotation_deg': round(rot, 2), 'shear_deg': round(math.degrees(math.acos(max(-1, min(1,
               -(T[0] * T[1] + T[3] * T[4]) / (sx * sy))))) - 90, 2) if sx and sy else None,
           'corners_lnglat': corners, 'residuals': res}
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
    print(f"{len(pts)} points, {out['model']} fit, RMS {out['rms_m']} m, "
          f"scale {out['scale_m_per_pt']} m/pt, rotation {out['rotation_deg']} deg, shear {out['shear_deg']} deg")
    for r in sorted(res, key=lambda r: -r.get('loo_err_m', r['err_m'])):
        print(f"  {r['id']:5} err {r['err_m']:6.1f} m" + (f"   left-out {r['loo_err_m']:6.1f} m" if 'loo_err_m' in r else ''))


if __name__ == '__main__':
    main()
