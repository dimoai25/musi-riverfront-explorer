"""Build the 'today' base map SVG page from colour groups of the window extract.
Usage: python3 -I today.py win.json out.html W H PX
"""
import sys, json
win, out = sys.argv[1], sys.argv[2]
W, H, PX = float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
P = json.load(open(win))
def key(p):
    return ('F ' + p['f']) if p['f'] != 'none' else ('S ' + p['s'])
G68 = 'S rgb(68.998718%, 68.998718%, 68.998718%)'
DOT = 'F rgb(57.598877%, 58.399963%, 59.599304%)'
RIV = 'S rgb(57.598877%, 58.399963%, 59.599304%)'
ORR = {'F rgb(0%, 100%, 0%)': '#b9c1c4', 'F rgb(100%, 100%, 0%)': '#6f7a80',
       'F rgb(0%, 0%, 100%)': '#6f7a80', 'S rgb(0%, 0%, 100%)': '#6f7a80'}
NALA = {'S rgb(0%, 86.698914%, 86.698914%)', 'F rgb(0%, 86.698914%, 86.698914%)', 'S rgb(0%, 100%, 100%)'}
layers = {'river': [], 'base': [], 'dot': [], 'orr': [], 'nala': []}
for p in P:
    k = key(p); fr = p['fr'] or 'nonzero'
    if k == G68:
        layers['base'].append(f'<path d="{p["d"]}"/>')
    elif k == DOT:
        layers['dot'].append(f'<path d="{p["d"]}" fill-rule="{fr}"/>')
    elif k == RIV:
        bb = p['bb']
        if max(bb[2]-bb[0], bb[3]-bb[1]) < 60: continue
        layers['river'].append(f'<path d="{p["d"]}"/>')
    elif k in ORR:
        c = ORR[k]
        if k.startswith('F'):
            layers['orr'].append(f'<path d="{p["d"]}" fill="{c}" fill-rule="{fr}"/>')
        else:
            layers['orr'].append(f'<path d="{p["d"]}" fill="none" stroke="{c}" stroke-width="{max(p["w"],0.5)}"/>')
    elif k in NALA:
        layers['nala'].append(f'<path d="{p["d"]}"/>')
h = PX * H / W
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{PX}" height="{h:.0f}" viewBox="0 0 {W} {H}" stroke-linecap="round" stroke-linejoin="round">'
       f'<rect width="{W}" height="{H}" fill="#f7f5ef"/>'
       f'<g opacity="0.55"><g fill="none" stroke="#b9dbe6" stroke-width="27">{"".join(layers["river"])}</g></g>'
       f'<g fill="none" stroke="#8fc3d6" stroke-width="0.9" stroke-dasharray="4 3">{"".join(layers["river"])}</g>'
       f'<g fill="none" stroke="#5fb1cc" stroke-width="1.6">{"".join(layers["nala"])}</g>'
       f'<g fill="#9b9790">{"".join(layers["dot"])}</g>'
       f'<g fill="none" stroke="#8d8a83" stroke-width="0.45">{"".join(layers["base"])}</g>'
       f'<g>{"".join(layers["orr"])}</g>'
       '</svg>')
open(out, 'w').write(f'<html><body style="margin:0">{svg}</body></html>')
print({k: len(v) for k, v in layers.items()})
