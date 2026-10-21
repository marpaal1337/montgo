"""Genera out/visor_3d.html: visor 3D estilo AllTrails (MapLibre + relieve) con las rutas de out/*.gpx."""
import glob, json, math, os
import xml.etree.ElementTree as ET

NS = {"g": "http://www.topografix.com/GPX/1/1"}
STATS = json.load(open("out/stats.json"))


def hav(a, b):
    r = 6371.0088
    p1, p2 = math.radians(a[1]), math.radians(b[1])
    dp, dl = p2 - p1, math.radians(b[0] - a[0])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


routes = {}
for key, s in STATS.items():
    root = ET.parse(f"out/{s['file']}.gpx").getroot()
    pts = [(float(p.get("lon")), float(p.get("lat")), float(p.find("g:ele", NS).text))
           for p in root.iterfind(".//g:trkpt", NS)]
    dist, d = [0.0], 0.0
    for a, b in zip(pts, pts[1:]):
        d += hav(a, b)
        dist.append(round(d, 4))
    wpts = [{"lon": float(w.get("lon")), "lat": float(w.get("lat")),
             "ele": float(w.find("g:ele", NS).text), "name": w.find("g:name", NS).text}
            for w in root.iterfind("g:wpt", NS)]
    routes[key] = {
        "name": s["name"], "km": round(s["km"], 2), "up": round(s["up"]), "dn": round(s["dn"]),
        "zmax": round(s["zmax"]), "maxslope": round(s["maxslope"]),
        "t_up": s["t_up"], "t_dn": s["t_dn"],
        "pts": [[round(x, 6), round(y, 6), round(z, 1)] for x, y, z in pts],
        "dist": dist, "wpts": wpts,
    }

html = open("scripts/viewer_template.html", encoding="utf-8").read()
html = html.replace("/*ROUTES*/null", json.dumps(routes, ensure_ascii=False))
open("out/visor_3d.html", "w", encoding="utf-8").write(html)
print("out/visor_3d.html", os.path.getsize("out/visor_3d.html") // 1024, "KB")
