'use strict';
/* Grabación de tracks GPS solo en el dispositivo (IndexedDB) con exportación a GPX; no hay servidor.
   Depende de app.js (map, styleReady, pad, $, esc, fmtH). Un fix es [lon, lat, ele|null, t en ms, precisión en m]. */
const Track = (() => {
  const MAX_ACC = 30, MIN_STEP = 8, SAVE_EVERY = 10, CLIMB_THR = 3;   // m, m, fixes, m
  const R = 6371008.8, rad = Math.PI / 180;
  const hav = (a, b) => {
    const dLat = (b[1] - a[1]) * rad, dLon = (b[0] - a[0]) * rad;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * rad) * Math.cos(b[1] * rad) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  };
  const fmtKm = m => (m / 1000).toFixed(2).replace('.', ',') + ' km';
  const when = t => new Date(t).toLocaleString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });

  /* ---------- almacenamiento ---------- */
  let dbp = null;
  const db = () => dbp ||= new Promise((res, rej) => {
    const q = indexedDB.open('cims', 1);
    q.onupgradeneeded = () => q.result.createObjectStore('tracks', { keyPath: 'id' });
    q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error);
  });
  const tx = (mode, fn) => db().then(d => new Promise((res, rej) => {
    const t = d.transaction('tracks', mode), r = fn(t.objectStore('tracks'));
    t.oncomplete = () => res(r.result); t.onerror = () => rej(t.error);
  }));

  /* ---------- estado ---------- */
  let rec = null, pending = null, msg = '', watchId = null, locating = false, centerNext = false;
  let wake = null, timer = null, unsaved = 0, last = null;

  const flush = () => { if (rec && unsaved) { unsaved = 0; tx('readwrite', s => s.put(rec)).catch(() => say('No se puede guardar en este navegador.')); } };
  function say(t) { msg = t; renderInfo(); }

  /* ---------- mapa ---------- */
  const empty = { type: 'FeatureCollection', features: [] };
  const lineOf = pts => pts.length < 2 ? empty : { type: 'Feature', geometry: { type: 'LineString', coordinates: pts.map(p => [p[0], p[1]]) } };
  const LAYERS = ['rec-case', 'rec-line', 'rec-halo', 'rec-pos'];
  styleReady.then(() => {
    const c = css('--rT') || '#d6336c';
    map.addSource('rec', { type: 'geojson', data: empty });
    map.addSource('rec-pos', { type: 'geojson', data: empty });
    map.addLayer({ id: 'rec-case', type: 'line', source: 'rec', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#fff', 'line-width': 7 } });
    map.addLayer({ id: 'rec-line', type: 'line', source: 'rec', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': c, 'line-width': 4 } });
    map.addLayer({ id: 'rec-halo', type: 'circle', source: 'rec-pos', paint: { 'circle-radius': 14, 'circle-color': '#1971c2', 'circle-opacity': .25 } });
    map.addLayer({ id: 'rec-pos', type: 'circle', source: 'rec-pos', paint: { 'circle-radius': 7, 'circle-color': '#1971c2', 'circle-stroke-color': '#fff', 'circle-stroke-width': 3 } });
  });
  const setLine = pts => { const s = map.getSource('rec'); if (s) s.setData(lineOf(pts)); };
  const setPos = f => { const s = map.getSource('rec-pos'); if (s) s.setData(f ? { type: 'Feature', geometry: { type: 'Point', coordinates: [f[0], f[1]] } } : empty); };
  const raise = () => LAYERS.forEach(id => { if (map.getLayer(id)) map.moveLayer(id); });   // las rutas se añaden después y taparían el track

  /* ---------- geolocalización ---------- */
  function startWatch() {
    if (watchId != null) return;
    watchId = navigator.geolocation.watchPosition(onPos, onErr, { enableHighAccuracy: true, maximumAge: 2000, timeout: 20000 });
  }
  function stopWatch() {
    if (watchId == null) return;
    navigator.geolocation.clearWatch(watchId); watchId = null; last = null; setPos(null);
  }
  function onErr(e) {
    if (e.code === 1) { say('Permiso de ubicación denegado.'); if (rec) stop(); locating = false; $('locBtn').setAttribute('aria-pressed', 'false'); stopWatch(); }
    else if (e.code === 3) say('Sin señal GPS por ahora…');
  }
  function onPos(pos) {
    const c = pos.coords, f = [c.longitude, c.latitude, c.altitude, pos.timestamp, Math.round(c.accuracy)];
    last = f; setPos(f);
    if (centerNext) { centerNext = false; map.easeTo({ center: [f[0], f[1]], zoom: Math.max(map.getZoom(), 15), duration: 800 }); }
    if (!rec || f[4] > MAX_ACC) return;
    const prev = rec.pts[rec.pts.length - 1];
    if (prev && hav(prev, f) < MIN_STEP) return;
    if (prev) rec.dist += hav(prev, f);
    if (f[2] != null) {   // desnivel con histéresis para no sumar el ruido del GPS
      if (rec.ref == null) rec.ref = f[2];
      else if (Math.abs(f[2] - rec.ref) >= CLIMB_THR) { if (f[2] > rec.ref) rec.up += f[2] - rec.ref; rec.ref = f[2]; }
    }
    rec.pts.push(f); rec.t1 = pos.timestamp; setLine(rec.pts);
    if (++unsaved >= SAVE_EVERY) flush();
    renderInfo();
  }

  /* ---------- pantalla encendida (el navegador pausa el GPS con la pantalla bloqueada) ---------- */
  async function lockScreen() {
    try { if ('wakeLock' in navigator && !wake) { wake = await navigator.wakeLock.request('screen'); wake.onrelease = () => { wake = null; renderInfo(); }; } } catch (e) { wake = null; }
    renderInfo();
  }
  const unlockScreen = () => { if (wake) wake.release().catch(() => {}); wake = null; };

  /* ---------- grabar / parar ---------- */
  function begin(t) {
    rec = t; rec.open = true; unsaved = 1; flush(); setLine(rec.pts);
    startWatch(); lockScreen(); timer = setInterval(renderInfo, 1000); msg = ''; renderInfo(); renderBtn();
  }
  function start() {
    if (pending) finish();
    begin({ id: Date.now(), t0: Date.now(), t1: Date.now(), pts: [], dist: 0, up: 0, ref: null, open: true });
  }
  function stop() {
    clearInterval(timer); timer = null; unlockScreen();
    const t = rec; rec = null; t.open = false;
    if (!locating) stopWatch();
    if (t.pts.length < 2) { tx('readwrite', s => s.delete(t.id)).catch(() => {}); setLine([]); say('Grabación demasiado corta: descartada.'); }
    else { tx('readwrite', s => s.put(t)).catch(() => {}); say('Guardado: ' + fmtKm(t.dist) + '. Descárgalo en «Tracks».'); }
    renderBtn(); renderList();
  }
  function finish() {   // cierra una grabación que quedó abierta (se cerró la página sin parar)
    const t = pending; pending = null; t.open = false;
    tx('readwrite', s => t.pts.length < 2 ? s.delete(t.id) : s.put(t)).catch(() => {});
    renderInfo(); renderList();
  }

  /* ---------- GPX ---------- */
  const x = s => String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  function toGPX(t) {
    const pts = t.pts.map(p => `<trkpt lat="${p[1].toFixed(6)}" lon="${p[0].toFixed(6)}">` + (p[2] != null ? `<ele>${p[2].toFixed(1)}</ele>` : '') + `<time>${new Date(p[3]).toISOString()}</time></trkpt>`);
    return `<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="Cims valencians" xmlns="http://www.topografix.com/GPX/1/1">\n<trk><name>${x('Track ' + when(t.t0))}</name><trkseg>\n${pts.join('\n')}\n</trkseg></trk>\n</gpx>\n`;
  }
  function download(t) {
    const d = new Date(t.t0), p = n => String(n).padStart(2, '0');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([toGPX(t)], { type: 'application/gpx+xml' }));
    a.download = `track-${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}.gpx`;
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  function view(t) {
    setLine(t.pts);
    const b = new maplibregl.LngLatBounds(); t.pts.forEach(p => b.extend([p[0], p[1]]));
    map.fitBounds(b, { padding: pad(), maxZoom: 16, duration: 900 });
  }

  /* ---------- interfaz ---------- */
  function renderBtn() {
    const b = $('recBtn'); b.textContent = rec ? '■ Parar' : '● Grabar'; b.classList.toggle('on', !!rec); b.setAttribute('aria-pressed', !!rec);
  }
  function renderInfo() {
    const el = $('recInfo'); let h = '';
    if (rec) {
      const hrs = (Date.now() - rec.t0) / 3.6e6;
      h = `<b class="dot">●</b> ${fmtKm(rec.dist)} · ${fmtH(hrs)} · +${Math.round(rec.up)} m` +
          `<small>${wake ? 'Pantalla activa mientras grabas.' : 'Mantén la pantalla encendida para no perder el GPS.'}${last ? ' Precisión ±' + last[4] + ' m.' : ' Buscando GPS…'}</small>`;
    } else if (pending) {
      h = `Grabación sin cerrar (${fmtKm(pending.dist)}, ${when(pending.t0)}).<span class="rrow"><button type="button" class="rbtn" data-act="resume">Reanudar</button><button type="button" class="rbtn" data-act="finish">Terminar</button></span>`;
    } else if (msg) h = esc(msg);
    el.hidden = !h; el.innerHTML = h;
  }
  function renderList() {
    tx('readonly', s => s.getAll()).then(all => {
      all = all.filter(t => !t.open && t.pts.length > 1).sort((a, b) => b.t0 - a.t0);
      $('tracksList').innerHTML = all.length ? all.map(t =>
        `<li data-id="${t.id}"><span><b>${when(t.t0)}</b> ${fmtKm(t.dist)} · +${Math.round(t.up)} m</span>` +
        `<button type="button" class="rbtn" data-act="view">Ver</button><button type="button" class="rbtn" data-act="gpx">GPX</button>` +
        `<button type="button" class="rbtn" data-act="del" aria-label="Borrar">✕</button></li>`).join('') : '<li class="mut">Aún no hay tracks guardados.</li>';
    }).catch(() => { $('tracksList').innerHTML = '<li class="mut">Almacenamiento no disponible.</li>'; });
  }

  function init() {
    if (!('geolocation' in navigator) || !isSecureContext || !('indexedDB' in window)) {
      $('rec').hidden = true; return;   // geolocalización exige HTTPS o localhost
    }
    $('recBtn').onclick = () => rec ? stop() : start();
    $('locBtn').onclick = () => {
      locating = !locating; $('locBtn').setAttribute('aria-pressed', locating);
      if (locating) {
        startWatch();
        if (last) map.easeTo({ center: [last[0], last[1]], zoom: Math.max(map.getZoom(), 15), duration: 800 }); else centerNext = true;
      } else if (!rec) stopWatch();
    };
    $('tracksBtn').onclick = () => {
      const open = $('tracksBox').hidden; $('tracksBox').hidden = !open; $('tracksBtn').setAttribute('aria-expanded', open); if (open) renderList();
    };
    $('rec').addEventListener('click', e => {
      const b = e.target.closest('[data-act]'); if (!b) return;
      const act = b.dataset.act, id = +b.closest('li')?.dataset.id;
      if (act === 'resume') { const t = pending; pending = null; begin(t); }
      else if (act === 'finish') finish();
      else tx('readonly', s => s.get(id)).then(t => {
        if (!t) return;
        if (act === 'view') view(t); else if (act === 'gpx') download(t);
        else if (act === 'del' && confirm('¿Borrar este track?')) tx('readwrite', s => s.delete(id)).then(renderList);
      });
    });
    document.addEventListener('visibilitychange', () => { if (document.hidden) flush(); else if (rec) lockScreen(); });
    addEventListener('pagehide', flush);
    tx('readonly', s => s.getAll()).then(all => {
      pending = all.find(t => t.open) || null;
      if (pending) { setLine(pending.pts); renderInfo(); }
    }).catch(() => {});
    renderBtn();
  }
  init();
  return { hav, raise };
})();
