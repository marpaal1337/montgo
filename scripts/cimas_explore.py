"""Ayuda para curar rutas: lista senderos señalizados que pasan junto a la cumbre y posibles salidas.
Uso: python scripts/cimas_explore.py <id>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import cimas_lib as L

pid = sys.argv[1]
peak = next(p for p in json.load(open("data/cimas/peaks.json")) if p["id"] == pid)
osm = json.load(open(f"data/cimas/{pid}_osm.json"))
S = (peak["lat"], peak["lon"])
ways = {e["id"]: e for e in osm["elements"] if e["type"] == "way"}
print(f"== {peak['name']} {peak['ele']} m ==\nSenderos señalizados con algún tramo a <400 m de la cumbre:")
for r in (e for e in osm["elements"] if e["type"] == "relation" and "members" in e):
    best = min((L.hav((g["lat"], g["lon"]), S) for m in r["members"] if m["type"] == "way" and m["ref"] in ways
                for g in ways[m["ref"]]["geometry"]), default=1e9)
    if best < 400:
        t = r["tags"]
        print(f"  rel {r['id']:>9} {t.get('network','-'):>4} {t.get('ref','-'):<12} {t.get('name','')[:70]}  (a {best:.0f} m; dist={t.get('distance','?')})")
print("Salidas posibles (aparcamientos / refugios / fuentes) ordenados por distancia a la cumbre:")
pts = []
for e in osm["elements"]:
    if e["type"] in ("way", "relation") and "tags" not in e: continue
    t = e.get("tags", {})
    if e["type"] == "way" and "highway" in t: continue
    c = (e["lat"], e["lon"]) if "lat" in e else (e["center"]["lat"], e["center"]["lon"]) if "center" in e else None
    kind = t.get("amenity") or t.get("tourism") or t.get("natural")
    if c and kind in ("parking", "alpine_hut", "wilderness_hut", "camp_site", "shelter", "spring", "drinking_water"):
        pts.append((L.hav(c, S), kind, t.get("name", ""), c))
for d, kind, name, c in sorted(pts)[:45]:
    print(f"  {d/1000:5.2f} km  {kind:<15} {name[:38]:<38} {c[0]:.5f},{c[1]:.5f}")
