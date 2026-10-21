"""Convierte out/ruta_*.gpx a out/ruta_*.kml (altitud absoluta, para Google Earth)."""
import glob
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

NS = {"g": "http://www.topografix.com/GPX/1/1"}
COL = {"A": "ff0859e8", "B": "ffd6881c", "C": "ffb5369c"}  # aabbggrr

for f in sorted(glob.glob("out/ruta_*.gpx")):
    root = ET.parse(f).getroot()
    name = root.find(".//g:trk/g:name", NS).text
    coords = " ".join(f"{p.get('lon')},{p.get('lat')},{p.find('g:ele', NS).text}"
                      for p in root.iterfind(".//g:trkpt", NS))
    wpts = "".join(
        f"<Placemark><name>{escape(w.find('g:name', NS).text)}</name><Point><altitudeMode>clampToGround</altitudeMode>"
        f"<coordinates>{w.get('lon')},{w.get('lat')},{w.find('g:ele', NS).text}</coordinates></Point></Placemark>"
        for w in root.iterfind("g:wpt", NS))
    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>{escape(name)}</name>
<Style id="t"><LineStyle><color>{COL[name[0]]}</color><width>4</width></LineStyle></Style>
<Placemark><name>{escape(name)}</name><styleUrl>#t</styleUrl><LineString><tessellate>1</tessellate>
<altitudeMode>clampToGround</altitudeMode><coordinates>{coords}</coordinates></LineString></Placemark>
{wpts}</Document></kml>"""
    open(f.replace(".gpx", ".kml"), "w", encoding="utf-8").write(kml)
    print(f.replace(".gpx", ".kml"))
