"""Warp a frame raster layer into standard Web Mercator XYZ tiles for MapLibre.

Usage:
  python3 -I tools/warp_tiles.py georef.json LAYER_SRC out_dir [--bg R,G,B] [--zmin 11] [--zmax 17] [--q 80]

LAYER_SRC is either a native frame raster (PNG, 13925 x 10500 px, 2.5 px per frame point) or a
v2 tile folder such as site/tiles/proposed (its native-zoom JSON bundles are stitched back into
the full raster, so the repo alone is enough to rebuild). Blank tiles were not stored in the
bundles, so pass the layer background with --bg (proposed 255,255,255; today 247,245,239; plan none).

Writes out_dir/{z}/{x}/{y}.webp (RGBA; outside the drawing is transparent, empty tiles are skipped)
and out_dir/tiles.json with the zoom range and the lng/lat bounds.

The deepest zoom is sampled straight from the source with 2x supersampling (bilinear); every
shallower zoom is a 2x2 box reduction of the one below, so there is no aliasing at low zoom.
"""
import base64, io, json, math, os, sys
import numpy as np
from PIL import Image

PX_PER_PT = 2.5
T256 = 256


def load_source(src, bg=None):
    if os.path.isdir(src):
        meta = json.load(open(os.path.join(src, 'meta.json')))
        W, H, z = meta['width'], meta['height'], meta['maxZoom']
        img = np.zeros((H, W, 4), np.uint8)
        if bg:  # tiles equal to the background were not stored; fill them back in
            img[:] = list(bg) + [255]
        for name in meta['bundles'][str(z)]:
            for key, b64 in json.load(open(os.path.join(src, f'z{z}_{name}.json'))).items():
                tx, ty = map(int, key.split('_'))
                t = np.asarray(Image.open(io.BytesIO(base64.b64decode(b64))).convert('RGBA'))
                y0, x0 = ty * T256, tx * T256
                h, w = min(T256, H - y0), min(T256, W - x0)
                img[y0:y0 + h, x0:x0 + w] = t[:h, :w]
        return img
    return np.asarray(Image.open(src).convert('RGBA'))


def tile_lnglat(z, X, Y, n):
    """lng/lat of the centres of an n x n grid of samples over tile (z, X, Y)."""
    s = (np.arange(n) + 0.5) / n
    gx = (X + s) / 2 ** z
    gy = (Y + s) / 2 ** z
    lng = gx * 360 - 180
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * gy))))
    return np.meshgrid(lng, lat)


def sample(img, fx, fy):
    """Bilinear sample (premultiplied alpha) at raster pixel coords; outside -> transparent."""
    H, W = img.shape[:2]
    x0 = np.floor(fx).astype(np.int64); y0 = np.floor(fy).astype(np.int64)
    wx = (fx - x0)[..., None]; wy = (fy - y0)[..., None]
    out = np.zeros(fx.shape + (4,), np.float32)
    for dx, dy, w in ((0, 0, (1 - wx) * (1 - wy)), (1, 0, wx * (1 - wy)), (0, 1, (1 - wx) * wy), (1, 1, wx * wy)):
        xi, yi = x0 + dx, y0 + dy
        ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
        px = np.zeros(fx.shape + (4,), np.float32)
        v = img[yi[ok], xi[ok]].astype(np.float32)
        v[:, :3] *= v[:, 3:4] / 255
        px[ok] = v
        out += px * w
    return out  # premultiplied, float


def unpremultiply(a):
    rgba = a.copy()
    al = rgba[..., 3:4]
    with np.errstate(invalid='ignore', divide='ignore'):
        rgba[..., :3] = np.where(al > 0, rgba[..., :3] * 255 / al, 0)
    return np.clip(np.rint(rgba), 0, 255).astype(np.uint8)


def main():
    args = sys.argv[1:]
    opt = {'--zmin': 11, '--zmax': 17, '--q': 80}
    bg = None
    if '--bg' in args:
        i = args.index('--bg'); bg = tuple(map(int, args[i + 1].split(','))); del args[i:i + 2]
    for k in list(opt):
        if k in args:
            i = args.index(k); opt[k] = int(args[i + 1]); del args[i:i + 2]
    G = json.load(open(args[0])); src, out = args[1], args[2]
    zmin, zmax, q = opt['--zmin'], opt['--zmax'], opt['--q']
    img = load_source(src, bg)
    H, W = img.shape[:2]
    Ti, lat0, lng0, kx, ky = G['Tinv'], G['lat0'], G['lng0'], G['kx'], G['ky']

    lngs = [c[0] for c in G['corners_lnglat']]; lats = [c[1] for c in G['corners_lnglat']]
    def tile_range(z):
        n = 2 ** z
        x = lambda lng: int((lng + 180) / 360 * n)
        y = lambda lat: int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
        return x(min(lngs)), x(max(lngs)), y(max(lats)), y(min(lats))

    SS = 2
    level = {}
    x0, x1, y0, y1 = tile_range(zmax)
    for X in range(x0, x1 + 1):
        for Y in range(y0, y1 + 1):
            lng, lat = tile_lnglat(zmax, X, Y, T256 * SS)
            E = (lng - lng0) * kx; N = (lat - lat0) * ky
            fx = (Ti[0] * E + Ti[1] * N + Ti[2]) * PX_PER_PT - 0.5
            fy = (Ti[3] * E + Ti[4] * N + Ti[5]) * PX_PER_PT - 0.5
            if fx.max() < -1 or fy.max() < -1 or fx.min() > W or fy.min() > H:
                continue
            a = sample(img, fx, fy)
            a = a.reshape(T256, SS, T256, SS, 4).mean(axis=(1, 3), dtype=np.float32)
            if a[..., 3].max() < 1:
                continue
            level[(X, Y)] = a
    counts = {}
    for z in range(zmax, zmin - 1, -1):
        os.makedirs(os.path.join(out, str(z)), exist_ok=True)
        for (X, Y), a in level.items():
            d = os.path.join(out, str(z), str(X)); os.makedirs(d, exist_ok=True)
            Image.fromarray(unpremultiply(a), 'RGBA').save(os.path.join(d, f'{Y}.webp'), 'WEBP', quality=q, method=6)
        counts[z] = len(level)
        if z == zmin:
            break
        parent = {}
        for (X, Y), a in level.items():
            P = parent.setdefault((X // 2, Y // 2), np.zeros((T256 * 2, T256 * 2, 4), np.float32))
            ox, oy = (X % 2) * T256, (Y % 2) * T256
            P[oy:oy + T256, ox:ox + T256] = a
        level = {k: v.reshape(T256, 2, T256, 2, 4).mean(axis=(1, 3)) for k, v in parent.items()}
    json.dump({'minzoom': zmin, 'maxzoom': zmax, 'bounds': [min(lngs), min(lats), max(lngs), max(lats)],
               'tiles': counts}, open(os.path.join(out, 'tiles.json'), 'w'))
    print(out, counts)


if __name__ == '__main__':
    main()
