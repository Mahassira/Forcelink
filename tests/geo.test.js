// Run: node tests/geo.test.js
'use strict';
const assert = require('assert');
const G = require('../static/assets/js/geo.js');
const EPS = 1e-9;
const near = (a, b, e = EPS) => Math.abs(a - b) <= e;
const vdist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
let passed = 0;
const t = (name, fn) => { fn(); passed++; console.log('ok -', name); };

t('lat/lon round-trip for all markets and base', () => {
  [G.BASE, ...G.MARKETS].forEach(p => {
    const v = G.latLonToVec(p.lat, p.lon, 1);
    assert(near(Math.hypot(v.x, v.y, v.z), 1), 'unit radius for ' + p.label);
    const back = G.vecToLatLon(v);
    assert(near(back.lat, p.lat, 1e-6), p.label + ' lat ' + back.lat);
    let dl = Math.abs(back.lon - p.lon);
    dl = Math.min(dl, 360 - dl);
    assert(dl < 1e-6, p.label + ' lon ' + back.lon);
  });
});

t('arc endpoints coincide with Dubai and each destination marker', () => {
  G.MARKETS.forEach(m => {
    const pts = G.arcPoints(G.BASE, m, { radius: 1, lift: 0.28, segments: 48 });
    const start = G.latLonToVec(G.BASE.lat, G.BASE.lon, 1);
    const end = G.latLonToVec(m.lat, m.lon, 1);
    assert(vdist(pts[0], start) < 1e-9, m.label + ' start');
    assert(vdist(pts[pts.length - 1], end) < 1e-9, m.label + ' end');
  });
});

t('arcs lie above the surface everywhere except the endpoints', () => {
  G.MARKETS.forEach(m => {
    const pts = G.arcPoints(G.BASE, m, { radius: 1, lift: 0.28, segments: 48 });
    pts.forEach((p, i) => {
      const r = Math.hypot(p.x, p.y, p.z);
      if (i === 0 || i === pts.length - 1) return;
      assert(r > 1 + 1e-6, m.label + ' point ' + i + ' radius ' + r);
      assert(r <= 1.28 + 1e-6, m.label + ' peak within lift');
    });
  });
});

t('arc is a smooth curve: no large jumps between consecutive points', () => {
  G.MARKETS.forEach(m => {
    const pts = G.arcPoints(G.BASE, m, { radius: 1, lift: 0.28, segments: 96 });
    let maxStep = 0;
    for (let i = 1; i < pts.length; i++) maxStep = Math.max(maxStep, vdist(pts[i], pts[i - 1]));
    assert(maxStep < 0.06, m.label + ' max step ' + maxStep);
  });
});

t('pointAlong returns the endpoints at 0 and 1 and stays on the curve', () => {
  const pts = G.arcPoints(G.BASE, G.MARKETS[0], { segments: 40 });
  const a = G.pointAlong(pts, 0);
  const b = G.pointAlong(pts, 1);
  assert(vdist(a, pts[0]) < 1e-12 && vdist(b, pts[pts.length - 1]) < 1e-12);
  const mid = G.pointAlong(pts, 0.5);
  assert(Math.hypot(mid.x, mid.y, mid.z) > 1, 'midpoint is lifted');
});

t('Europe is represented as a single regional point, not a country', () => {
  const eu = G.MARKETS.find(m => m.key === 'europe');
  assert(eu && /region/i.test(eu.label));
  assert.strictEqual(G.MARKETS.length, 6);
});

t('all six reported destinations are present', () => {
  const labels = G.MARKETS.map(m => m.label.replace(' (region)', '')).sort();
  assert.deepStrictEqual(labels, ['China', 'Europe', 'India', 'Indonesia', 'Malaysia', 'Vietnam']);
});

console.log(`\n${passed} tests passed`);
