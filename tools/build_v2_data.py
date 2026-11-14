"""Assemble v2 explorer data (stops, features, docs, stretches) in frame points.
Frame = master plan sheet 1 page points minus (30, 420). Raster is 2.5 px per point.
Usage: python3 -I build_v2_data.py v1data.json placed.json out.json
"""
import json, sys, re, math, hashlib

v1 = json.load(open(sys.argv[1]))
P = json.load(open(sys.argv[2]))
OX, OY = 30, 420                      # page -> frame
WX, WY = 440, 260                     # v1 window -> frame (window origin 470,680 on page)

def pg(x, y): return [round(x - OX, 1), round(y - OY, 1)]

# Builder and gated-community names were removed from v1data.json before it was committed.
# The build refuses any output that contains them, checked by hashed word so the names
# themselves never appear in this public repo.
BLOCKED = ['01cc438379207fe6', '3cafcab6534313b8', '74112fe3bd45284e', '89ca7cc5290a28fe', '8c3869450fcdb063', 'b38623b1ac7f8b53', 'ff99fea6321216db']
def blocked_words(s):
    return sorted({w for w in re.findall(r'[A-Za-z]+', s)
                   if hashlib.sha256(w.lower().encode()).hexdigest()[:16] in BLOCKED})

assert not blocked_words(json.dumps(v1)), blocked_words(json.dumps(v1))

chain = P['chain']
def at(z, c):
    L = chain[z]
    for (c1, x1, y1), (c2, x2, y2) in zip(L, L[1:]):
        if c1 <= c <= c2 and c2 > c1:
            t = (c - c1) / (c2 - c1); return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
    return (L[0][1], L[0][2]) if c < L[0][0] else (L[-1][1], L[-1][2])
def box(z, c0, c1, pad=70):
    pts = [(x, y) for c, x, y in chain[z] if c0 <= c <= c1] + [at(z, c0), at(z, c1)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return [round(min(xs) - pad - OX), round(min(ys) - pad - OY), round(max(xs) + pad - OX), round(max(ys) + pad - OY)]
def pin(z, c): return pg(*at(z, c))

SRC = {
 'w': ["Proposed master plan, Zone 1A & 1B: sheet 1 (MHT-MP-PP-01-Z1) and the Zone 1B part plans, Meinhardt for MRDCL, Rev R02, Sep 2026.",
       "Road layout plans (1ROADS-1), sheets 1 to 3: Ch 0+720 to 5+640.",
       "Design Basis Report, Roads and Bridges: Table 2-1 (roads) and Table 2-3 (Osman Sagar to Bapughat bridges).",
       "Design Basis Report, Rubber Dams (Zones A and B): dams at Ch 2.550, 3.690 and 4.980 km.",
       "Employer's Requirements 6.26 (landscaping) and the ESMP, for parks and impacts."],
 'e': ["Proposed master plan, Zone 1A & 1B: sheet 1 (MHT-MP-PP-01-Z1), the eastern Zone 1B part plans and sheet 7 (Gandhi Sarovar and Bapu Ghat), Rev R02, Sep 2026.",
       "Road layout plans (1ROADS-1), sheets 4 to 7: Ch 5+640 to Gandhi Sarovar.",
       "Design Basis Report, Roads and Bridges: Table 2-1 (roads) and Table 2-3, bridges 6 to 9 (Vyas Nagar, Ibrahimbagh, Tipu Khan, Bapu Ghat).",
       "Design Basis Report, Rubber Dams (Zones A and B): dams at Ch 6.270, 8.040, 8.760 and 10.410 km."],
 'a': ["Proposed master plan, Zone 1A & 1B: sheet 1 (MHT-MP-PP-01-Z1), Rev R02, Sep 2026. This sheet shows Zone 1A at the same level of detail as Zone 1B; the Zone 1B part plans and road sheets do not cover Zone 1A.",
       "Design Basis Report, Roads and Bridges: Table 2-1 (Zone 1A roads) and Table 2-2 (Himayat Sagar to Bapughat bridges).",
       "Design Basis Report, Rubber Dams (Zones A and B): Zone 1A dams at Ch 4.140, 5.520, 6.900 and 7.830 km.",
       "Not used: Zone 1A's own construction tender (contract 06/CE/MRDCL/2026-27). Its drawings may add detail that isn't on sheet 1."],
}

stops = []
ov = v1['STOPS'][0]
stops.append({
 'id': 'overview', 'n': 0, 'short': 'Overview', 'stretch': None,
 'name': 'Musi Riverfront Phase 1: Zone 1A and 1B',
 'ch': 'About 21 km of river · Osman Sagar and Himayat Sagar to Bapu Ghat',
 'box': [0, 0, 5570, 4200],
 'lead': "This map covers the whole of Phase 1, Zone 1 on the tender master plan: Zone 1B along the Musi from Osman Sagar to Bapu Ghat (about 12 km), and Zone 1A along the Esi from Himayat Sagar to Bapu Ghat (about 9 km). Pick a stretch below, then step through its stops. Drag the handle on the map to compare today with the plan.",
 'pickers': True,
 'nums': [["21 km", "of river: about 12 km on the Musi (Zone 1B) and 9 km on the Esi (Zone 1A)"],
          ["15", "vehicle bridges across both rivers, including the cable-stayed bridge over the ORR"],
          ["11", "rubber dams holding back pools of water"],
          ["5", "parking and activity nodes with multi-level car parking"]],
 'sections': [
   ["Status", "", ["Zone 1B is out to construction (EPC) tender, contract 07/CE/MRDCL/2026-27. Zone 1A has its own tender, contract 06/CE/MRDCL/2026-27.",
                   "Every drawing is stamped \"issued for planning and tender only\" and \"all dimensions tentative\". The master plan used here is Rev R02, Sep 2026.",
                   "Positions on this map come from the plan's own survey base, so the plan and the base line up with each other. Matching them to an exact plot needs the official cadastral drawings."]],
   ["How to read the map", "var(--river)", ["Light blue is the proposed river bed, grey bands with lane lines are proposed roads, orange is the promenade and green is parks and landscape.",
                   "The outer edge of the works on each bank (roads, promenades and the drawn site lines) shows roughly how much land the plan uses there.",
                   "Today is the survey base inside the master plan: buildings, roads, nalas and an approximate river course."]],
   ["Watch-outs across the corridor", "", ["The ESMP counts about 639 affected structures and about 2,660 affected trees across Zone 1.",
                   "Parts of the works fall inside the 10 km eco-sensitive buffer of Mrugavani National Park, which needs wildlife-board (NBWL) clearance.",
                   "Land acquisition for the project is being challenged in the Telangana High Court; some landowners have interim protection.",
                   "Footbridges are marked \"not included in DPR\", so treat them as uncertain."]]],
})

# --- stretch W: v1 overview becomes the stretch intro; v1 stops shifted into the frame
stops.append({
 'id': 'west', 'n': 0, 'short': 'Intro', 'stretch': 'w', 'intro': True,
 'name': 'Gandipet to Narsingi', 'ch': 'Zone 1B · Musi · Ch 0+600 to 5+940 · about 5.3 km',
 'box': [WX, WY, WX + 2190, WY + 1140],
 'lead': "The first stretch of Zone 1B, from the Osman Sagar dam at Gandipet, round the river bend and over the Outer Ring Road to the Vyas Nagar junctions at Narsingi and Manchirevula.",
 'nums': ov['nums'],
 'sections': [s for s in ov['sections'] if s[0] == 'How the corridor works'],
 'sources': SRC['w'],
})
for s in v1['STOPS'][1:]:
    if s.get('docs'): continue
    s = dict(s)
    s['stretch'] = 'w'
    s['pin'] = [s['pin'][0] + WX, s['pin'][1] + WY]
    b = s['box']; s['box'] = [b[0] + WX, b[1] + WY, b[2] + WX, b[3] + WY]
    stops.append(s)

# --- stretch E: Zone 1B Narsingi to Bapu Ghat
stops.append({
 'id': 'east', 'n': 0, 'short': 'Intro', 'stretch': 'e', 'intro': True,
 'name': 'Narsingi to Bapu Ghat', 'ch': 'Zone 1B · Musi · Ch 5+940 to 12+212 · about 6.3 km',
 'box': box('1B', 5900, 12270, 90),
 'lead': "East of the Vyas Nagar junctions the river runs past Manchirevula, Bairagiguda and Hydershahkote to the Gandhi Sarovar site and Bapu Ghat, where the Esi (Zone 1A) joins it.",
 'nums': [["3", "vehicle bridges: Ibrahimbagh, Tipu Khan and Bapu Ghat"], ["4", "rubber dams"],
          ["1", "parking and activity node, at Gandhi Sarovar"], ["2", "footbridges, marked not included in DPR"]],
 'sections': [["How the corridor works", "var(--river)", [
     "The 30 m main road continues along the river to about Ch 9+650, where the roads report links it to an \"elevated corridor\". That corridor is not detailed in these documents.",
     "A 15 m service road runs on the left bank from the ORR service road to the Ibrahimbagh bridge (Ch 5+030 to 6+780).",
     "At the east end, a 30 m peripheral road of about 1.6 km around Gandhi Sarovar and a 15 m link road (Ch 10+100 to 10+700) tie into Langar Houz, Attapur and the PVNR Expressway."]]],
 'sources': SRC['e'],
})
stops += [
 {'id': 'stop-8', 'n': 8, 'short': '8', 'stretch': 'e', 'name': 'Manchirevula to Ibrahimbagh', 'ch': 'Ch 5+940 to 7+500',
  'pin': pin('1B', 6600), 'box': box('1B', 5900, 7500), 'chips': ['Ibrahimbagh bridge', 'Rubber dam'],
  'sections': [
    ["Today", "var(--muted)", ["The river runs east past Manchirevula. The survey base shows housing and plotted layouts close to the river on both banks for much of this reach."]],
    ["Connectivity", "var(--river)", ["Ibrahimbagh bridge (Ch 6+600): 34 m wide, six lanes, at a slight skew. The roads report pairs it with a 350 m, 30 m-wide road north to the Shankarpally highway.",
                                      "A 15 m service road runs on the left bank from the ORR service road to the bridge.",
                                      "The 30 m main road continues east along the river."]],
    ["Landscape and public space", "var(--park)", ["Glow Parklet at the western end, by the Vyas Nagar junctions.", "A \"Broadwalk Trail\" theme is marked along this reach.", "A rubber dam at Ch 6.27 km holds a pool of water upstream."]]],
  'watch': ["Bridge widths and spans come from a draft design basis report and can change."],
  'look': [["Road layout plans", "sheet 4 (Ch 5+640 to 7+260)"], ["Road and bridge DBR", "Table 2-3, bridge 7"], ["Rubber dams DBR", "the dam at Ch 6.270"]]},
 {'id': 'stop-9', 'n': 9, 'short': '9', 'stretch': 'e', 'name': 'Bairagiguda to Hydershahkote', 'ch': 'Ch 7+500 to 10+000',
  'pin': pin('1B', 8700), 'box': box('1B', 7500, 10000), 'chips': ['2 new junctions', '2 footbridges'],
  'sections': [
    ["Today", "var(--muted)", ["Dense neighbourhoods sit south of the river around Bairagiguda and Hydershahkote. The Bairagiguda nala joins from the south at about Ch 7.8 km."]],
    ["Connectivity", "var(--river)", ["New junctions at People Plaza (about Ch 7.9 km) and Hydershahkote village (about Ch 9.2 km) connect the riverfront road to the neighbourhoods.",
                                      "Two footbridges, PB 04 (about Ch 8.3 km) and PB 05 (about Ch 9.8 km), are drawn with lift and stair cores. Both are marked not included in DPR.",
                                      "A \"future road\" is also marked along this reach."]],
    ["Landscape and public space", "var(--park)", ["Landscaped Eco Park theme near Ch 9.4 km.", "Rubber dams at Ch 8.04 and 8.76 km."]]],
  'watch': ["The elevated corridor named in the roads report, from about Ch 9+650, is not detailed in these documents.", "Footbridges are outside the DPR, so treat them as uncertain."],
  'look': [["Road layout plans", "the sheets from Ch 7+260 eastward"], ["Rubber dams DBR", "the dams at Ch 8.040 and 8.760"]]},
 {'id': 'stop-10', 'n': 10, 'short': '10', 'c': True, 'stretch': 'e', 'name': 'Tipu Khan bridge and Gandhi Sarovar', 'ch': 'Ch 10+000 to 11+300',
  'pin': pin('1B', 10650), 'box': box('1B', 10000, 11300, 120), 'chips': ['Commercial node 3', 'Tipu Khan bridge'],
  'sections': [
    ["Today", "var(--muted)", ["The river passes north of the Gandhi Sarovar site. NH 163 and the roads from Hydershahkote, Narsingi and Chevella meet near the west side of the site."]],
    ["Connectivity", "var(--river)", ["Tipu Khan bridge (Ch 10+800, Gandhi Sarovar north-west): 34 m wide, six lanes, at a 45° skew.",
                                      "Two new junctions, Gandhi Sarovar West Junctions 1 and 2, connect it to the Hydershahkote, Narsingi and Chevella roads.",
                                      "A 30 m peripheral road of about 1.6 km circles the Gandhi Sarovar site."]],
    ["Parking and activity", "var(--node)", ["Commercial node 3: the plan marks \"Surface + Multi-level Car Parking (MLCP) - 3, along with ancillary facilities and Activity Generating Usages\" on the north bank by Shankerpally Road."]],
    ["Landscape and public space", "var(--park)", ["Tapovanam Park phase 2 on the north bank.", "Rubber dam at Ch 10.41 km."]]],
  'watch': ["A large \"Gandhi Sarovar development\" parcel is outlined south of the river. It is a separate project and this tender does not detail it."],
  'look': [["Proposed master plan", "sheet 7 (Gandhi Sarovar and Bapu Ghat)"], ["Road and bridge DBR", "Table 2-3, bridge 8"], ["Rubber dams DBR", "the dam at Ch 10.410"]]},
 {'id': 'stop-11', 'n': 11, 'short': '11', 'stretch': 'e', 'name': 'Bapu Ghat and the confluence', 'ch': 'Ch 11+300 to 12+212',
  'pin': pin('1B', 11800), 'box': box('1B', 11300, 12270, 140), 'chips': ['Bapu Ghat bridge', 'Esi joins here'],
  'sections': [
    ["Today", "var(--muted)", ["Bapu Ghat, with the Gandhi samadhi, the Gandhi museum, a temple area and a step well, sits on the north bank by Langar Houz. The Esi (Zone 1A) joins the Musi here."]],
    ["Connectivity", "var(--river)", ["Bapu Ghat bridge (Ch 11+900, Gandhi Sarovar north-east): 34 m wide, six lanes. It links Langar Houz on the north bank with Attapur and the PVNR Expressway on the south.",
                                      "An east–west corridor and a pedestrian Bapu Ghat bridge are drawn across the confluence."]],
    ["Landscape and tourism", "var(--park)", ["The existing Bapu Ghat features are kept, inside the Gandhi Sarovar / Tapovan Park (Tapovanam Park phase 1).",
                                              "A circular \"Island of Peace\" with a Gandhi tower is drawn at the confluence."]]],
  'watch': ["This is the busiest meeting point on the corridor: two rivers, the PVNR Expressway and several roads come together here."],
  'look': [["Proposed master plan", "sheet 7 (Gandhi Sarovar and Bapu Ghat)"], ["Road and bridge DBR", "Table 2-3, bridge 9"]]},
]

# --- stretch A: Zone 1A
stops.append({
 'id': 'zone-1a', 'n': 0, 'short': 'Intro', 'stretch': 'a', 'intro': True,
 'name': 'Himayat Sagar to Bapu Ghat (Zone 1A)', 'ch': 'Zone 1A · Esi · Ch 1+200 to 9+140 · about 8 km',
 'box': box('1A', 1200, 9100, 120),
 'lead': "Zone 1A follows the Esi from below the Himayat Sagar dam, under the ORR, past Budvel, Kismathpur and the Rajendranagar road, then north through Upparpally and Attapur to meet the Musi at Bapu Ghat.",
 'nums': [["6", "vehicle bridges"], ["4", "rubber dams"], ["2", "parking and activity nodes"], ["30 m", "main road from Kismathpur to Gandhi Sarovar, with 15 m service roads upstream"]],
 'sections': [["How the corridor works", "var(--river)", [
     "The roads report describes Zone 1A as largely greenfield, with little existing road along the river.",
     "15 m service roads run on both banks from Himayat Sagar to Kismathpur.",
     "From Kismathpur (Ch 3+690) a 30 m main road runs along the right bank to Gandhi Sarovar (Ch 9+140).",
     "The network links to the ORR service roads, Rajendranagar Road, Kismathpur, Budvel, Upparpally and Attapur."]],
   ["About this stretch's source", "", ["Zone 1A has its own construction tender, which I haven't used. Everything here comes from the joint master plan sheet, which shows Zone 1A in full detail, and from the Zone 1 design basis reports."]]],
 'sources': SRC['a'],
})
stops += [
 {'id': 'a-1', 'n': 'A1', 'short': 'A1', 'c': True, 'stretch': 'a', 'name': 'Himayat Sagar and the ORR', 'ch': 'Zone 1A · Ch 1+200 to 2+100',
  'pin': pin('1A', 1650), 'box': box('1A', 1150, 2150, 110), 'chips': ['Commercial node 4', '2 bridges'],
  'sections': [
    ["Today", "var(--muted)", ["The Esi leaves Himayat Sagar and passes under the Outer Ring Road. The survey base shows mostly open land on the south bank, housing set back on the north, and rock outcrops in the river bed."]],
    ["Connectivity", "var(--river)", ["Two 18 m bridges on either side of the ORR (Ch 1+200 and 1+295) carry the riverfront roads across the river next to the ORR.", "15 m service roads start on both banks here."]],
    ["Parking and activity", "var(--node)", ["Commercial node 4 (marked MLCP - 1 for Zone 1A): \"Surface + Multi-level Car Parking, along with ancillary facilities and Activity Generating Usages\" on the north bank, near Ch 2.0 km."]],
    ["Landscape and public space", "var(--park)", ["Natural Heritage Parklet and Forest Trail Parklet by the ORR, keeping the existing rock formations.",
                                                    "Picnic Lawn and Community Gathering Spaces, ghat steps and an \"activity generating usages\" area further east.",
                                                    "Footbridge PB 10, marked not included in DPR."]]],
  'look': [["Proposed master plan", "sheet 1 (the only sheet in this set that details Zone 1A)"], ["Road and bridge DBR", "Table 2-2, bridges 1 and 2"]]},
 {'id': 'a-2', 'n': 'A2', 'short': 'A2', 'stretch': 'a', 'name': 'Budvel bridge and Kismathpur', 'ch': 'Zone 1A · Ch 2+100 to 3+700',
  'pin': pin('1A', 2900), 'box': box('1A', 2100, 3700, 110), 'chips': ['Budvel bridge', 'Sports park'],
  'sections': [
    ["Today", "var(--muted)", ["The river runs east with Kismathpur on the north bank and mostly open plots to the south. The Kismathpur nala joins from the north."]],
    ["Connectivity", "var(--river)", ["Budvel bridge (Ch 2+550): 34 m wide, six lanes, on the road between Kismathpur and Rajendranagar.", "15 m service roads continue on both banks."]],
    ["Landscape and public space", "var(--park)", ["Wellness + Sports Park (HS Proposed Park 1) on the south bank, around Ch 3.3 km.", "Ghat steps along both banks and a footbridge marked not included in DPR."]]],
  'look': [["Proposed master plan", "sheet 1"], ["Road and bridge DBR", "Table 2-2, bridge 3"]]},
 {'id': 'a-3', 'n': 'A3', 'short': 'A3', 'c': True, 'stretch': 'a', 'name': 'Rajendranagar Road and the Agriculture University', 'ch': 'Zone 1A · Ch 3+700 to 4+600',
  'pin': pin('1A', 4000), 'box': box('1A', 3600, 4700, 130), 'chips': ['Commercial node 5', 'Kismathpur bridge'],
  'sections': [
    ["Today", "var(--muted)", ["The river turns north here. Rajendranagar Road and the road to Budvel village meet near the bank, and the Agriculture University nala joins from the east."]],
    ["Connectivity", "var(--river)", ["Kismathpur bridge (Ch 3+900): 34 m wide, six lanes, at the bend.",
                                      "A new junction ties the riverfront roads to Rajendranagar Road, Kismathpur and Budvel village.",
                                      "The 30 m main road starts here on the right bank (Ch 3+690) and runs north to Gandhi Sarovar."]],
    ["Parking and activity", "var(--node)", ["Commercial node 5 (marked MLCP - 2 for Zone 1A): \"Surface + Multi-level Car Parking, along with ancillary facilities and Activity Generating Usages\" beside the junction."]],
    ["Landscape and public space", "var(--park)", ["Natural Trail Parklet on the north-east bank.", "Rubber dam at Ch 4.14 km."]]],
  'watch': ["This is the nearest point on the corridor to the agricultural university campus at Rajendranagar. The campus itself is not drawn or named on the sheet; only the Agriculture University nala is."],
  'look': [["Proposed master plan", "sheet 1"], ["Road and bridge DBR", "Table 2-2, bridge 4"], ["Rubber dams DBR", "the dam at Ch 4.140"]]},
 {'id': 'a-4', 'n': 'A4', 'short': 'A4', 'stretch': 'a', 'name': 'Upparpally and Sun City', 'ch': 'Zone 1A · Ch 4+600 to 7+300',
  'pin': pin('1A', 6000), 'box': box('1A', 4600, 7300, 110), 'chips': ['Upparpally bridge', '2 rubber dams'],
  'sections': [
    ["Today", "var(--muted)", ["The river runs north between densely built neighbourhoods on both banks, the most built-up reach of Zone 1A."]],
    ["Connectivity", "var(--river)", ["Upparpally bridge (Ch 6+900): 34 m wide, six lanes, on the road from Sun City to Attapur and the PVNR Expressway.",
                                      "The 30 m main road runs along the right bank.", "Footbridge PB 08 near Ch 5.1 km, marked not included in DPR."]],
    ["Landscape and public space", "var(--park)", ["Rubber dams at Ch 5.52 and 6.90 km."]]],
  'watch': ["With housing close to both banks, the outer edge of the works runs near existing buildings in places. The overlay is approximate, so it can't tell you whether a particular building is affected."],
  'look': [["Proposed master plan", "sheet 1"], ["Road and bridge DBR", "Table 2-2, bridge 5"], ["Rubber dams DBR", "the dams at Ch 5.520 and 6.900"]]},
 {'id': 'a-5', 'n': 'A5', 'short': 'A5', 'stretch': 'a', 'name': 'Attapur to the confluence', 'ch': 'Zone 1A · Ch 7+300 to 9+140',
  'pin': pin('1A', 8000), 'box': box('1A', 7300, 9100, 120), 'chips': ['Bapu Ghat (Esi) bridge', 'Biodiversity park'],
  'sections': [
    ["Today", "var(--muted)", ["The river runs north past Attapur to meet the Musi at Gandhi Sarovar."]],
    ["Connectivity", "var(--river)", ["Bapu Ghat bridge over the Esi (Ch 8+200): 34 m wide, six lanes.", "Footbridge PB 06 near Ch 7.4 km, marked not included in DPR.", "The main road ends at Gandhi Sarovar (Ch 9+140)."]],
    ["Landscape and public space", "var(--park)", ["Children Parklet, Tree of Life Parklet and a Nature and Bio-diversity Park (HS Proposed Park 2).", "Rubber dam at Ch 7.83 km."]]],
  'look': [["Proposed master plan", "sheets 1 and 7"], ["Road and bridge DBR", "Table 2-2, bridge 6"], ["Rubber dams DBR", "the dam at Ch 7.830"]]},
]
stops.append({'id': 'documents', 'docs': True, 'short': 'Documents', 'stretch': None, 'name': 'The tender documents behind this map',
              'ch': 'Zone 1B tender documents, used for both zones', 'box': [0, 0, 5570, 4200]})

# --- features
feats = []
for f in v1['FEATURES']:
    f = dict(f)
    if f['t'] == 'place' and f['label'] in ('the bend',): continue
    f['x'] += WX; f['y'] += WY
    if f['t'] == 'node': f['code'] = 'C%d' % (f['i'] + 1)
    feats.append(f)
for c, n, w, x, y in P['items']['1B']['bridges']:
    if c < 6000: continue
    fx, fy = pg(x, y)
    feats.append({'t': 'bridge', 'x': fx, 'y': fy, 'label': n, 'sub': f"{w} m · Ch {c//1000}+{c%1000:03d}"})
for c, x, y in P['items']['1B']['dams']:
    if c < 6000: continue
    fx, fy = pg(x, y); feats.append({'t': 'dam', 'x': fx, 'y': fy, 'label': f"Rubber dam · Ch {c//1000}+{c%1000:03d}"})
for c, n, w, x, y in P['items']['1A']['bridges']:
    fx, fy = pg(x, y)
    feats.append({'t': 'bridge', 'x': fx, 'y': fy, 'label': n, 'sub': f"{w} m · Esi Ch {c//1000}+{c%1000:03d}"})
for c, x, y in P['items']['1A']['dams']:
    fx, fy = pg(x, y); feats.append({'t': 'dam', 'x': fx, 'y': fy, 'label': f"Rubber dam · Esi Ch {c//1000}+{c%1000:03d}"})
for code, label, (x, y), stop in [('C3', 'Commercial node 3', (5130, 1635), 'stop-10'), ('C4', 'Commercial node 4', (3832, 4023), 'a-1'), ('C5', 'Commercial node 5', (4668, 3962), 'a-3')]:
    fx, fy = pg(x, y); feats.append({'t': 'node', 'code': code, 'x': fx, 'y': fy, 'label': label, 'stop': stop})
for label, (x, y), extra in [
    ('Himayat Sagar', (2430, 4330), {'water': True, 'far': True}), ('Kismathpur', (3960, 3860), {}), ('Rajendranagar Rd', (4830, 4110), {}),
    ('Budvel', (4850, 3930), {}), ('Sun City', (4980, 2440), {}), ('Attapur', (5360, 2760), {'far': True}),
    ('Hydershahkote', (4700, 1920), {'far': True}), ('Langar Houz', (5480, 1585), {'far': True}), ('Bapu Ghat', (5440, 1640), {}),
    ('Gandhi Sarovar', (5180, 1800), {'far': True}), ('Bairagiguda', (3480, 1790), {}), ('Zone 1B', (2930, 1860), {'far': True, 'zone': True}),
    ('Zone 1A', (3930, 3420), {'far': True, 'zone': True})]:
    fx, fy = pg(x, y); f = {'t': 'place', 'x': fx, 'y': fy, 'label': label}; f.update(extra); feats.append(f)

docs = v1['DOCS']
stretches = [
  {'id': 'w', 'name': 'Gandipet to Narsingi', 'zone': 'Zone 1B', 'ch': 'Ch 0+600 to 5+940', 'first': 'west'},
  {'id': 'e', 'name': 'Narsingi to Bapu Ghat', 'zone': 'Zone 1B', 'ch': 'Ch 5+940 to 12+212', 'first': 'east'},
  {'id': 'a', 'name': 'Himayat Sagar to Bapu Ghat', 'zone': 'Zone 1A', 'ch': 'Ch 1+200 to 9+140', 'first': 'zone-1a'},
]
blob = json.dumps({'STOPS': stops, 'FEATURES': feats, 'DOCS': docs, 'STRETCHES': stretches, 'SOURCES': SRC}, ensure_ascii=False)
assert not blocked_words(blob), blocked_words(blob)
for bad in ("2027", "2028", "2029", "2030", "27 Nov"):  # no timelines on the public site
    assert bad not in blob, bad
json.dump(json.loads(blob), open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
print(len(stops), 'stops', len(feats), 'features')
