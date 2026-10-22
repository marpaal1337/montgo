'use strict';
/* PeakClusters: marcadores HTML de MapLibre que se agrupan solos cuando, con el zoom actual, sus etiquetas se solaparían.
   La agrupación se decide en píxeles de pantalla (map.project), así que funciona igual con el mapa inclinado o girado.
   Al pulsar un grupo la cámara se acerca a sus miembros y el grupo se deshace; un marcador suelto se comporta como siempre.

   const pc = new PeakClusters(map, peaks, {
     createPin: peak => HTMLElement,            // marcador de una cima, <button> (su data-label pasa a aria-label)
     createCluster: peaks => HTMLElement,       // marcador de un grupo (peaks ordenadas de mayor a menor altura)
     onSelect: peak => {},                      // clic en una cima suelta
     box: { w: 110, h: 36 },                    // tamaño aproximado de una etiqueta; dos etiquetas se solapan si |dx|<w y |dy|<h
     padding: () => ({}),                       // padding de la cámara al acercar a un grupo (p. ej. para esquivar paneles)
     maxZoom: 14 });
   pc.setFilter(setDeIds | null)  · pc.setEnabled(bool)  · pc.refresh()  · pc.highlight(id, bool)  · pc.destroy() */
class PeakClusters {
  constructor(map, items, opts) {
    this.map = map;
    this.items = [...items].sort((a, b) => b.ele - a.ele);   // la cima más alta ancla cada grupo
    this.o = { box: { w: 110, h: 36 }, padding: () => ({}), maxZoom: 14, onSelect: () => {}, ...opts };
    this.filter = null; this.enabled = true;
    this.live = new Map();        // clave de grupo → { marker, ids }
    this.keyOf = new Map();       // id de cima → clave del marcador que la representa ahora
    this._raf = 0;
    this._onMove = () => this._schedule();
    map.on('move', this._onMove);
    map.on('resize', this._onMove);
    this.update();
  }

  setFilter(ids) { this.filter = ids; this.update(); }
  setEnabled(on) { this.enabled = on; if (on) this.update(); else this._clear(); }
  refresh() { this._clear(); this.update(); }   // reconstruye los elementos (p. ej. al cambiar el estado «hecha»)
  destroy() { this.map.off('move', this._onMove); this.map.off('resize', this._onMove); cancelAnimationFrame(this._raf); this._clear(); }

  highlight(id, on) {
    const live = this.live.get(this.keyOf.get(id));
    live?.marker.getElement().classList.toggle('hl', on);
  }

  _schedule() { if (!this._raf) this._raf = requestAnimationFrame(() => { this._raf = 0; this.update(); }); }
  _clear() { this.live.forEach(l => l.marker.remove()); this.live.clear(); this.keyOf.clear(); }

  /* agrupación voraz: cada cima aún libre, de mayor a menor altura, absorbe a las libres cuya etiqueta se le solapa */
  _groups() {
    const { w, h } = this.o.box;
    const pts = this.items.filter(p => !this.filter || this.filter.has(p.id)).map(p => ({ p, s: this.map.project([p.lon, p.lat]) }));
    const taken = new Set(), groups = [];
    for (const a of pts) {
      if (taken.has(a.p.id)) continue;
      taken.add(a.p.id);
      const g = [a.p];
      for (const b of pts) {
        if (taken.has(b.p.id)) continue;
        if (Math.abs(a.s.x - b.s.x) < w && Math.abs(a.s.y - b.s.y) < h) { taken.add(b.p.id); g.push(b.p); }
      }
      groups.push(g);
    }
    return groups;
  }

  update() {
    if (!this.enabled) return;
    const groups = this._groups(), keep = new Set();
    this.keyOf.clear();
    for (const g of groups) {
      const key = g.map(p => p.id).join('+');
      keep.add(key);
      g.forEach(p => this.keyOf.set(p.id, key));
      if (this.live.has(key)) continue;   // mismo grupo que antes: se reutiliza el marcador
      const el = g.length === 1 ? this.o.createPin(g[0]) : this.o.createCluster(g);
      if (g.length === 1) el.onclick = () => this.o.onSelect(g[0]);
      else el.onclick = () => this._zoomTo(g);
      const lon = g.reduce((s, p) => s + p.lon, 0) / g.length, lat = g.reduce((s, p) => s + p.lat, 0) / g.length;
      const marker = new maplibregl.Marker({ element: el, anchor: 'bottom' }).setLngLat([lon, lat]).addTo(this.map);
      if (el.dataset.label) el.setAttribute('aria-label', el.dataset.label);   // MapLibre pone «Map marker» al crear el marcador
      this.live.set(key, { marker, ids: g.map(p => p.id) });
    }
    for (const [key, l] of this.live) if (!keep.has(key)) { l.marker.remove(); this.live.delete(key); }
  }

  /* acerca la cámara a los miembros del grupo; garantiza al menos +1 de zoom para que el grupo se deshaga */
  _zoomTo(g) {
    const b = new maplibregl.LngLatBounds();
    g.forEach(p => b.extend([p.lon, p.lat]));
    const cam = this.map.cameraForBounds(b, { padding: this.o.padding() });
    const z = Math.min(this.o.maxZoom, Math.max(cam ? cam.zoom - 0.3 : 0, this.map.getZoom() + 1));
    this.map.easeTo({ center: cam ? cam.center : b.getCenter(), zoom: z, duration: 800, padding: this.o.padding() });
  }
}
