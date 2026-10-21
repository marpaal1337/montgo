# Montgó · domingo 25-oct-2026 · 5 amigos desde Valencia

## Comparativa (generada con OSM + EU-DEM 25 m; subida = una vía)
| Ruta | Km | Desnivel + | Alt. salida | Subida / bajada* | Carácter |
|---|---|---|---|---|---|
| **A** Directa campo de tiro Les Planes (PR-CV 355) | 3,35 (publicado 3,87) | +526 m | 212 m | 1h30 / 0h30 | Corta y empinada (media ~16 %, máx ~58 %); cresta final con trepada |
| **C** Camí de la Colònia (Dénia, ruta naranja) | 5,84 (publicado ~6) | +821 m | 52 m | 2h30 / 1h00 | Pista larga y suave y último km muy empinado (hasta ~72 %), piedra suelta |
| **B** Larga Jesús Pobre · GR-330 · Creueta de Dénia | 8,88 | +742 m | 74 m | 3h00 / 1h30 | La más larga y gradual, sin trepada fuerte; la más tranquila |

*Naismith (5 km/h + 1 h/600 m) para un grupo sin parar; con 5 personas, fotos y comida suma ~+25 %.

Archivos: `out/ruta_*.gpx` (track + waypoints), `out/perfil_A|B|C.png`, `out/perfil_comparativo.png`, `out/stats.json`.

## Recomendación
- **Grupo en forma que quiere ir a lo seguro de tiempo: A.** Señalizada (PR-CV 355), la más corta y la más cercana a Valencia. Cuidado con la cresta final (manos).
- **Si queréis una excursión más larga: B**, más gradual. Evita la trepada fuerte.
- **C** solo si os gusta el último km a tope; es la de más desnivel.
- Las 3 son ida y vuelta por el mismo track (GPX de subida).

## Logística
- Valencia → Les Planes/Dénia: ~105-110 km, ~1h15 por AP-7 (salida de Valencia 7:00 para empezar sobre las 8:30).
- **Ojo: esa noche cambia la hora (cambio a horario de invierno, 03:00 → 02:00).** Puesta de sol ≈ 18:15; estar abajo antes de las 17:00.
- 2-3 L de agua por persona, calzado con suela de montaña, cortavientos, frontal por si acaso. Sin fuentes en ruta.

## Avisos importantes
- **Temporal / alerta roja 18-19 oct en la Marina Alta**: puede haber sendas dañadas o piedra suelta; revisar el estado.
- Posibles restricciones por riesgo de incendio (nivel 3 prohíbe senderos). Confirmar con el Parque: parque_montgo@gva.es · 966 427 155.
- El AEMET solo llega al sábado 24 (15/22 °C, 0-10 % lluvia). El domingo 25: mirar la previsión el sábado por la tarde.

## Limitaciones del track (honestas)
- Rutas calculadas sobre sendas de OpenStreetMap, no son grabaciones GPS. Las distancias salen ~10-13 % por debajo de las publicadas en la ruta A.
- La **circular clásica de Jesús Pobre por el Barranc de l'Hedra (6,27 km, +746 m, 3h45) no está conectada en OSM**, por eso B es la variante larga por GR-330. Para la clásica, descargar el GPX de Wikiloc 49391841 (requiere login).
- El DEM suaviza la cumbre (≈735 m frente a 752 m reales); el waypoint de cumbre usa 752 m.
- Cotejar con Wikiloc / Komoot antes de salir.

Regenerar: `python scripts/fetch_osm.py data/osm.json && python scripts/build_routes.py` (necesita matplotlib y networkx).
