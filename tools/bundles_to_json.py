"""Convert .bin tile bundles to .json bundles {"x_y": "<base64 webp>"}. Usage: python3 -I bundles_to_json.py layer_dir"""
import sys, os, json, struct, base64
d = sys.argv[1]
n = 0
for f in sorted(os.listdir(d)):
    if not f.endswith('.bin'): continue
    raw = open(os.path.join(d, f), 'rb').read()
    hl = struct.unpack('<I', raw[:4])[0]; idx = json.loads(raw[4:4 + hl]); base = 4 + hl
    out = {k: base64.b64encode(raw[base + o: base + o + l]).decode() for k, (o, l) in idx.items()}
    json.dump(out, open(os.path.join(d, f[:-4] + '.json'), 'w'), separators=(',', ':'))
    os.remove(os.path.join(d, f)); n += 1
print(d, n, 'bundles')
