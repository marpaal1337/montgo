"""Propone hasta 3 rutas (A, B, C) por cima sin rutas definidas en data/cimas/routes.json, eligiendo las mejores
salidas candidatas de sectores distintos. Revisar el resultado (build_cimas avisa de puntos lejos de la red).
Uso: python scripts/cimas_autoroutes.py [id ...]"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import cimas_lib as L

peaks = json.load(open("data/cimas/peaks.json"))
defs = json.load(open("data/cimas/routes.json"))
want = set(sys.argv[1:])


def pick(cands, n=3):
    chosen = []
    for min_gap, new_sector in ((400, True), (600, False)):
        for sec, km, frac, name, kind, c, oid in cands:
            if len(chosen) == n: break
            if new_sector and any(sec == s for s, _ in chosen): continue
            if any(L.hav(c, o) < min_gap for _, o in chosen): continue
            chosen.append((sec, c))
    return chosen


for p in peaks:
    if (want and p["id"] not in want) or p["id"] in defs:
        continue
    f = f"data/cimas/{p['id']}_osm.json"
    if not os.path.exists(f):
        print(p["id"], "sin OSM descargado"); continue
    osm = json.load(open(f))
    d0, cands = L.candidates(p, osm, 3.0, 12.0)
    ch = pick(cands)
    if len(ch) < 3:   # zonas con pocas salidas: ampliar el rango de distancia
        d0, cands = L.candidates(p, osm, 2.0, 18.0)
        ch = pick(cands)
    print(f"{p['id']:<24} red a {d0:4.0f} m de la cumbre, {len(ch)} salidas")
    if not ch:
        continue
    S = [p["lat"], p["lon"]]
    defs[p["id"]] = [{"id": "ABC"[i], "start_pt": [round(c[0], 5), round(c[1], 5)], "via": [[round(c[0], 5), round(c[1], 5)], S]}
                     for i, (_, c) in enumerate(ch)]
    json.dump(defs, open("data/cimas/routes.json", "w"), indent=1)
