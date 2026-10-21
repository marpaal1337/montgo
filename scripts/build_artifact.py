"""Genera out/visor_3d_artifact.html: visor autocontenido (three.js + relieve y mapa incrustados) para publicar como artifact."""
import json, os, re

# reutiliza el parseo de rutas de build_viewer.py sin reescribir el HTML del visor MapLibre
src = open("scripts/build_viewer.py", encoding="utf-8").read()
exec(src.split('html = open(')[0])

terrain = json.load(open("data/terreno.json"))
html = open("scripts/artifact_template.html", encoding="utf-8").read()
html = html.replace("/*ROUTES*/null", json.dumps(routes, ensure_ascii=False))
html = html.replace("/*TERRAIN*/null", json.dumps(terrain))
html = html.replace("/*SHARED*/", open("scripts/shared.js", encoding="utf-8").read())
open("out/visor_3d_artifact.html", "w", encoding="utf-8").write(html)
print("out/visor_3d_artifact.html", os.path.getsize("out/visor_3d_artifact.html") // 1024, "KB")

js = re.findall(r"<script>(.*?)</script>", html, re.S)[0]
open(os.environ.get("JS_OUT", "/dev/null"), "w").write(js)
