"""Descarga de OSM la red de sendas, relaciones de senderismo y puntos de interés alrededor de cada cima.
Uso: python scripts/cimas_fetch.py [id ...]   → data/cimas/<id>_osm.json (regenerable, no se versiona)"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import cimas_lib as L

R = 0.07   # grados alrededor de la cima (~7,8 km de lado a lado en latitud)
peaks = json.load(open("data/cimas/peaks.json"))
want = set(sys.argv[1:])
for p in peaks:
    if want and p["id"] not in want:
        continue
    out = f"data/cimas/{p['id']}_osm.json"
    if os.path.exists(out):
        print(p["id"], "ya descargado"); continue
    b = f"{p['lat']-R:.5f},{p['lon']-R*1.25:.5f},{p['lat']+R:.5f},{p['lon']+R*1.25:.5f}"
    q = f"""[out:json][timeout:150];
(
  way["highway"~"^(path|track|footway|steps|bridleway|service|unclassified|tertiary|tertiary_link|residential)$"]({b});
);
out geom;
(
  relation["route"~"^(hiking|foot)$"]({b});
);
out body;
(
  nwr["amenity"~"^(parking|shelter|drinking_water)$"]({b});
  nwr["natural"="spring"]({b});
  nwr["tourism"~"^(alpine_hut|wilderness_hut|camp_site)$"]({b});
);
out tags center;"""
    print(p["id"], "descargando…")
    d = L.overpass(q)
    json.dump(d, open(out, "w"))
    print("  ", len(d["elements"]), "elementos,", os.path.getsize(out) // 1024, "KB")
