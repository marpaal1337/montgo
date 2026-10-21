/* ---- lógica común al visor local y al artifact: posición del sol y color por pendiente ---- */
const SUN = { lat: 38.80, lon: 0.13, n: 298, tz: 1 };   // 25-oct-2026, Montgó, hora local = UTC+1 (ya en horario de invierno)
const RAD = Math.PI / 180;
function sunPos(h) {
  const B = 360 / 365 * (SUN.n - 81) * RAD;
  const eot = 9.87 * Math.sin(2 * B) - 7.53 * Math.cos(B) - 1.5 * Math.sin(B);   // minutos
  const decl = -23.44 * Math.cos(360 / 365 * (SUN.n + 10) * RAD) * RAD;
  const H = (h - SUN.tz + SUN.lon / 15 + eot / 60 - 12) * 15 * RAD, phi = SUN.lat * RAD;
  const el = Math.asin(Math.sin(phi) * Math.sin(decl) + Math.cos(phi) * Math.cos(decl) * Math.cos(H));
  const az = Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(phi) - Math.tan(decl) * Math.cos(phi));
  return { el: el / RAD, az: (az / RAD + 180 + 360) % 360 };   // acimut desde el norte, sentido horario
}
const SUN_RISE_SET = (() => {
  let rise = null, set = null;
  for (let h = 3; h < 22; h += 1 / 60) {
    const up = sunPos(h).el > -0.83;   // borde superior del disco con refracción
    if (up && rise === null) rise = h;
    if (!up && rise !== null && set === null) set = h;
  }
  return { rise, set };
})();
const fmtClock = h => { const m = Math.round(h * 60); return Math.floor(m / 60) + ':' + String(m % 60).padStart(2, '0'); };
const COMPASS = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'];
const compass = az => COMPASS[Math.round(az / 45) % 8];
function sunInfo(h) {
  const s = sunPos(h);
  return s.el > 0 ? `Altura ${Math.round(s.el)}° · ${compass(s.az)} · sale ${fmtClock(SUN_RISE_SET.rise)}, se pone ${fmtClock(SUN_RISE_SET.set)}`
                  : `Sol bajo el horizonte · sale ${fmtClock(SUN_RISE_SET.rise)}, se pone ${fmtClock(SUN_RISE_SET.set)}`;
}

/* pendiente (%) por punto, suavizada sobre ~80 m */
function slopeSeries(r) {
  const n = r.pts.length;
  return r.pts.map((_, i) => {
    let a = i, b = i;
    while (a > 0 && r.dist[i] - r.dist[a] < 0.04) a--;
    while (b < n - 1 && r.dist[b] - r.dist[i] < 0.04) b++;
    const dd = (r.dist[b] - r.dist[a]) * 1000;
    return dd > 0 ? Math.abs(r.pts[b][2] - r.pts[a][2]) / dd * 100 : 0;
  });
}
const SLOPE_STOPS = [[0, [61, 154, 74]], [10, [140, 198, 63]], [20, [242, 194, 48]], [30, [238, 125, 28]], [45, [209, 45, 45]], [60, [91, 16, 16]]];
function slopeRGB(s) {
  if (s <= 0) return SLOPE_STOPS[0][1];
  for (let i = 1; i < SLOPE_STOPS.length; i++) {
    const [s1, c1] = SLOPE_STOPS[i];
    if (s <= s1) { const [s0, c0] = SLOPE_STOPS[i - 1], t = (s - s0) / (s1 - s0); return c0.map((v, j) => v + (c1[j] - v) * t); }
  }
  return SLOPE_STOPS[SLOPE_STOPS.length - 1][1];
}
const slopeHex = s => '#' + slopeRGB(s).map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
function slopeAtDist(r, d) {
  if (!r.slope) r.slope = slopeSeries(r);
  let i = 1;
  while (i < r.dist.length - 1 && r.dist[i] < d) i++;
  return r.slope[i];
}
const LEGEND_CSS = `linear-gradient(90deg, ${SLOPE_STOPS.map(([s, c]) => `rgb(${c.join(',')}) ${s / 60 * 100}%`).join(', ')})`;
