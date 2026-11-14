"""Cut a large raster into a z0..Z pyramid of 256px WebP tiles, packed into 8x8 bundles.
Usage: python3 -I tile_bundles.py in.png out_dir bg_r,bg_g,bg_b quality [rgba]
Bundle format: uint32 LE header length, UTF-8 JSON {"x_y":[offset,len]}, then WebP bytes (offsets from data start).
"""
import sys, os, io, json, struct
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
src, out, bg, q = sys.argv[1], sys.argv[2], tuple(int(v) for v in sys.argv[3].split(',')), int(sys.argv[4])
rgba = len(sys.argv) > 5 and sys.argv[5] == 'rgba'
os.makedirs(out, exist_ok=True)
im = Image.open(src).convert('RGBA' if rgba else 'RGB')
W, H = im.size
Z = 0
while 256 * 2 ** Z < max(W, H): Z += 1
T, B = 256, 8
meta = {'width': W, 'height': H, 'maxZoom': Z, 'tile': T, 'bundle': B, 'bundles': {}}
total = 0
for z in range(Z, -1, -1):
    f = 2 ** (Z - z)
    lvl = im if f == 1 else im.resize((max(1, round(W / f)), max(1, round(H / f))), Image.LANCZOS)
    lw, lh = lvl.size
    nx, ny = -(-lw // T), -(-lh // T)
    arr = np.asarray(lvl)
    bundles = {}
    for ty in range(ny):
        for tx in range(nx):
            t = arr[ty*T:(ty+1)*T, tx*T:(tx+1)*T]
            if rgba:
                if t[..., 3].max() < 8: continue
            else:
                if np.abs(t.astype(np.int16) - np.array(bg, np.int16)).max() <= 6: continue
            tile = Image.fromarray(t)
            if tile.size != (T, T):
                canvas = Image.new(tile.mode, (T, T), (0, 0, 0, 0) if rgba else bg); canvas.paste(tile, (0, 0)); tile = canvas
            buf = io.BytesIO(); tile.save(buf, 'WEBP', quality=q, method=4)
            bundles.setdefault((tx // B, ty // B), []).append((f'{tx}_{ty}', buf.getvalue()))
    keys = []
    for (bx, by), items in bundles.items():
        idx, off, data = {}, 0, []
        for k, b in items: idx[k] = [off, len(b)]; off += len(b); data.append(b)
        hdr = json.dumps(idx, separators=(',', ':')).encode()
        with open(f'{out}/z{z}_{bx}_{by}.bin', 'wb') as fh:
            fh.write(struct.pack('<I', len(hdr))); fh.write(hdr); [fh.write(b) for b in data]
        keys.append(f'{bx}_{by}'); total += off
    meta['bundles'][z] = keys
    print('z', z, 'tiles', sum(len(v) for v in bundles.values()), 'bundles', len(bundles))
json.dump(meta, open(f'{out}/meta.json', 'w'))
print('MB', round(total / 1e6, 2))
