import json, math, networkx as nx

PEN = {"path": 1.0, "track": 1.1, "footway": 1.1, "steps": 1.3, "service": 1.8,
       "unclassified": 2.5, "tertiary": 4, "tertiary_link": 4, "residential": 3}

def hav(a, b):
    R = 6371008.8
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dl = math.radians(b[1] - a[1]); dp = p2 - p1
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

def load(path="data/osm.json"):
    d = json.load(open(path))
    G = nx.Graph(); pos = {}
    for e in d["elements"]:
        if e["type"] != "way" or "highway" not in e.get("tags", {}):
            continue
        hw = e["tags"]["highway"]
        pen = PEN.get(hw, 3)
        ids, geo = e["nodes"], e["geometry"]
        for i, g in zip(ids, geo):
            pos[i] = (g["lat"], g["lon"])
        for i in range(len(ids) - 1):
            a, b = ids[i], ids[i+1]
            L = hav(pos[a], pos[b])
            if G.has_edge(a, b) and G[a][b]["w"] <= L*pen:
                continue
            G.add_edge(a, b, w=L*pen, len=L, hw=hw, name=e["tags"].get("name"), way=e["id"])
    return G, pos

def nearest(G, pos, pt, only=None):
    best = min((hav(pos[n], pt), n) for n in G.nodes if only is None or any(G[n][m]["hw"] in only for m in G[n]))
    return best[1], best[0]

def route(G, pos, pts):
    """pts: list of (lat,lon) waypoints (snapped); returns list of node ids."""
    nodes = []
    for a, b in zip(pts, pts[1:]):
        na, _ = nearest(G, pos, a); nb, _ = nearest(G, pos, b)
        p = nx.shortest_path(G, na, nb, weight="w")
        nodes += p if not nodes else p[1:]
    return nodes
