"""Extract vector paths inside a window from a pdftocairo SVG.
Usage: python3 -I extract.py in.svg out.json x0 y0 x1 y1
Output: list of {d (window coords, 1 decimal), f (fill), s (stroke), w (stroke width), fr (fill rule)}
"""
import sys, re, json
import xml.etree.ElementTree as ET

src, out = sys.argv[1], sys.argv[2]
X0, Y0, X1, Y1 = map(float, sys.argv[3:7])
NUM = re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')
TOK = re.compile(r'[MLCZmlcz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')

def parse_matrix(t):
    if not t: return (1,0,0,1,0,0)
    m = re.search(r'matrix\(([^)]*)\)', t)
    if not m: return (1,0,0,1,0,0)
    v = [float(x) for x in NUM.findall(m.group(1))]
    return tuple(v)

def tx(m, x, y):
    a,b,c,d,e,f = m
    return a*x + c*y + e, b*x + d*y + f

def conv(d, m):
    toks = TOK.findall(d)
    outp = []; xs=[]; ys=[]
    i = 0; cmd = None
    while i < len(toks):
        t = toks[i]
        if t in 'MLCZmlcz':
            cmd = t; i += 1
            if t in 'Zz': outp.append('Z')
            continue
        n = 6 if cmd in 'Cc' else 2
        vals = [float(v) for v in toks[i:i+n]]; i += n
        pts = []
        for k in range(0, n, 2):
            X, Y = tx(m, vals[k], vals[k+1])
            X -= X0; Y -= Y0
            xs.append(X); ys.append(Y)
            pts.append(f"{X:.1f} {Y:.1f}")
        outp.append(cmd.upper() + ' '.join(pts))
    if not xs: return None, None
    return ''.join(outp), (min(xs), min(ys), max(xs), max(ys))

W, H = X1 - X0, Y1 - Y0
res = []
for ev, el in ET.iterparse(src, events=("end",)):
    tag = el.tag.split('}')[1]
    if tag == 'path':
        d = el.get('d')
        if d:
            m = parse_matrix(el.get('transform'))
            nd, bb = conv(d, m)
            if bb and bb[2] >= 0 and bb[0] <= W and bb[3] >= 0 and bb[1] <= H:
                sw = el.get('stroke-width')
                scale = (abs(m[0]*m[3]-m[1]*m[2]))**0.5
                res.append({'d': nd, 'f': el.get('fill', 'none'), 's': el.get('stroke', 'none'),
                            'w': round(float(sw)*scale, 2) if sw else 0, 'fr': el.get('fill-rule', ''),
                            'bb': [round(v, 1) for v in bb]})
        el.clear()
    elif tag in ('g', 'mask', 'image', 'use'):
        pass
json.dump(res, open(out, 'w'))
print(len(res), 'paths in window')
