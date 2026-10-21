import json, re, xml.etree.ElementTree as ET, math
NS = {"g": "http://www.topografix.com/GPX/1/1"}
FILES = {"A": "ruta_A_campo_tiro_Les_Planes", "C": "ruta_C_Cami_de_la_Colonia", "B": "ruta_B_larga_Jesus_Pobre_GR330"}
stats = json.load(open("out/stats.json"))
R = {}
for k, f in FILES.items():
    t = ET.parse(f"out/{f}.gpx")
    pts = [(float(p.get("lat")), float(p.get("lon")), float(p.find("g:ele", NS).text)) for p in t.iterfind(".//g:trkpt", NS)]
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        dy = (b[0]-a[0])*111195; dx = (b[1]-a[1])*111195*math.cos(math.radians(a[0]))
        d.append(d[-1] + math.hypot(dx, dy))
    R[k] = dict(pts=pts, d=d, **stats[k])

def hm(h):
    m = round(h*60/5)*5
    return f"{m//60}h{m%60:02d}"

# ---------- profile chart ----------
def profile(keys, w=720, h=270, xmax=None):
    L, Rr, T, B = 46, 14, 14, 34
    xmax = xmax or max(R[k]["d"][-1] for k in keys)/1000
    xmax = math.ceil(xmax)
    ymin, ymax = 0, 800
    X = lambda km: L + (w-L-Rr)*km/xmax
    Y = lambda z: T + (h-T-B)*(1 - (z-ymin)/(ymax-ymin))
    s = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" xmlns="http://www.w3.org/2000/svg">']
    for z in range(0, 801, 200):
        s.append(f'<line x1="{L}" x2="{w-Rr}" y1="{Y(z):.1f}" y2="{Y(z):.1f}" class="grid"/><text x="{L-8}" y="{Y(z)+4:.1f}" class="tick" text-anchor="end">{z}</text>')
    for km in range(0, xmax+1):
        s.append(f'<text x="{X(km):.1f}" y="{h-12}" class="tick" text-anchor="middle">{km}</text>')
    s.append(f'<text x="{w-Rr}" y="{h-1}" class="tick" text-anchor="end">km</text><text x="4" y="10" class="tick">m</text>')
    for k in keys:
        r = R[k]; step = max(1, len(r["pts"])//140)
        idx = list(range(0, len(r["pts"]), step)); idx = idx + ([len(r["pts"])-1] if idx[-1] != len(r["pts"])-1 else [])
        xy = [(X(r["d"][i]/1000), Y(r["pts"][i][2])) for i in idx]
        line = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
        if len(keys) == 1:
            s.append(f'<polygon points="{xy[0][0]:.1f},{Y(0):.1f} {line} {xy[-1][0]:.1f},{Y(0):.1f}" class="fill-{k}"/>')
        s.append(f'<polyline points="{line}" class="line line-{k}"/>')
        ex, ey = xy[-1]
        s.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4.5" class="dot dot-{k}"/>')
        if len(keys) > 1:
            s.append(f'<text x="{ex-8:.1f}" y="{ey-9:.1f}" class="lbl lbl-{k}" text-anchor="end">{k}</text>')
    if len(keys) == 1:
        ex, ey = xy[-1]
        s.append(f'<text x="{ex-10:.1f}" y="{ey-10:.1f}" class="lbl" text-anchor="end">Cumbre 752 m</text>')
    s.append('</svg>')
    return "".join(s)

# ---------- plan map ----------
def planmap(w=720, h=330):
    allp = [p for r in R.values() for p in r["pts"]]
    c = math.cos(math.radians(38.81))
    lons = [p[1]*c for p in allp]; lats = [p[0] for p in allp]
    x0, x1, y0, y1 = min(lons), max(lons), min(lats), max(lats)
    pad = 34
    sc = min((w-2*pad)/(x1-x0), (h-2*pad)/(y1-y0))
    ox = (w-(x1-x0)*sc)/2; oy = (h-(y1-y0)*sc)/2
    P = lambda p: (ox+(p[1]*c-x0)*sc, h-oy-(p[0]-y0)*sc)
    s = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" xmlns="http://www.w3.org/2000/svg">']
    for k in "BCA":
        pts = R[k]["pts"]
        s.append('<polyline points="' + " ".join(f"{P(p)[0]:.1f},{P(p)[1]:.1f}" for p in pts[::2] + [pts[-1]]) + f'" class="line line-{k}"/>')
    off = {"A": (-10, 18, "end"), "B": (10, 18, "start"), "C": (-10, -10, "end")}
    for k in "ABC":
        x, y = P(R[k]["pts"][0]); dx, dy, anc = off[k]
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" class="dot dot-{k}"/><text x="{x+dx:.1f}" y="{y+dy:.1f}" class="lbl lbl-{k}" text-anchor="{anc}">Salida {k}</text>')
    x, y = P(R["A"]["pts"][-1])
    s.append(f'<path d="M{x:.1f},{y-9:.1f} l8,14 h-16 z" class="peak"/><text x="{x+13:.1f}" y="{y+4:.1f}" class="lbl">Cumbre 752 m</text>')
    s.append(f'<g transform="translate({w-26},26)"><path d="M0,-12 l5,16 l-5,-4 l-5,4 z" class="north"/><text y="20" class="tick" text-anchor="middle">N</text></g></svg>')
    return "".join(s)

def card(k, title, sub, notes, start_name):
    r = R[k]; p0 = r["pts"][0]
    return f'''<article class="route r-{k}" id="ruta-{k.lower()}">
  <header><span class="badge b-{k}">{k}</span><div><h3>{title}</h3><p class="sub">{sub}</p></div></header>
  <dl class="facts">
    <div><dt>Distancia</dt><dd>{r["km"]:.1f} km</dd></div>
    <div><dt>Desnivel</dt><dd>+{r["up"]:.0f} m</dd></div>
    <div><dt>Salida</dt><dd>{r["zmin"]:.0f} m</dd></div>
    <div><dt>Subida</dt><dd>{hm(r["t_up"]*1.25)}</dd></div>
    <div><dt>Bajada</dt><dd>{hm(r["t_dn"]*1.25)}</dd></div>
  </dl>
  {profile([k], xmax=r["d"][-1]/1000)}
  <ul class="notes">{"".join(f"<li>{n}</li>" for n in notes)}</ul>
  <p class="coord"><span>{start_name}</span> <code>{p0[0]:.5f}, {p0[1]:.5f}</code>
  <button type="button" class="copy" data-copy="{p0[0]:.5f}, {p0[1]:.5f}">Copiar</button>
  <a href="https://www.google.com/maps/search/?api=1&amp;query={p0[0]:.5f},{p0[1]:.5f}" target="_blank" rel="noopener">Abrir en Google Maps</a></p>
</article>'''

cards = card("A", "Directa desde el campo de tiro", "Les Planes, PR‑CV 355 · la que recomiendo", [
    "Corta y constante. Pendiente media cercana al 16 %.",
    "Último tramo por la cresta caliza: hay que usar las manos en un par de pasos.",
    "Está señalizada y es la más cercana a Valencia."], "Campo de tiro (Les Planes)") + \
  card("C", "Camí de la Colònia", "Desde Dénia, ruta naranja del Parque", [
    "Primeros 4 km de pista suave, casi llana.",
    "El último kilómetro sube de golpe, con piedra suelta. Aquí se gana casi todo el desnivel.",
    "Es la que más desnivel acumula."], "Inicio del camino (Dénia)") + \
  card("B", "Larga por Jesús Pobre", "GR‑330 y Creueta de Dénia", [
    "Subida gradual y sin trepadas fuertes. Es la más tranquila.",
    "Con un grupo de cinco y paradas, cuenta con unas 4 horas de subida.",
    "No es la circular clásica por el Barranc de l'Hedra (ver avisos)."], "Jesús Pobre")

rows = ""
for k in "ACB":
    r = R[k]
    rows += f'<tr><th scope="row"><span class="badge b-{k}">{k}</span></th><td>{r["km"]:.1f} km</td><td>+{r["up"]:.0f} m</td><td>{hm(r["t_up"]*1.25)}</td><td>{hm(r["t_dn"]*1.25)}</td><td>{ {"A":"Corta y empinada","C":"Pista y último km duro","B":"Larga y gradual"}[k] }</td></tr>'

html = open("scripts/report_template.html").read()
for key, val in {"{{PROFILE_ALL}}": profile(list("ACB")), "{{MAP}}": planmap(), "{{CARDS}}": cards, "{{ROWS}}": rows}.items():
    html = html.replace(key, val)
open("out/informe.html", "w").write(html)
print(len(html))
