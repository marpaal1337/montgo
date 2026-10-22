"""Propone salidas candidatas (una por sector de orientación) para cada cima, enrutando desde la cumbre sobre OSM.
Uso: python scripts/cimas_candidates.py <id> [km_min km_max]"""
import heapq, json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import cimas_lib as L

pid = sys.argv[1]
kmin, kmax = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (3.0, 12.0)
peak = next(p for p in json.load(open("data/cimas/peaks.json")) if p["id"] == pid)
osm = json.load(open(f"data/cimas/{pid}_osm.json"))
d0, cands = L.candidates(peak, osm, kmin, kmax)
print(f"== {peak['name']}: nodo de red a {d0:.0f} m de la cumbre")
best = {}
for sec, km, frac, name, kind, c, oid in cands:
    best.setdefault(sec, []).append((km, frac, name, kind, c, oid))
print("sector(desde cumbre) | km ruta | % sendero/pista | tipo | nombre | lat,lon")
for sec in sorted(best):
    for km, frac, name, kind, c, oid in best[sec][:2]:
        print(f"  {['N','NE','E','SE','S','SO','O','NO'][sec]:<2} {km:5.1f} km {frac*100:4.0f}%  {kind:<9} {name[:34]:<34} {c[0]:.5f},{c[1]:.5f}")
