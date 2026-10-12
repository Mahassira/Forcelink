/* Market-connections globe (Three.js). Loaded only on the home page.
   - Dotted sphere, Dubai base marker, six curved arcs to the reported destination markets.
   - Light pulses travel from Dubai along each arc. Frame-rate independent (time-based).
   - Paused when off-screen; static render when prefers-reduced-motion is set.
   - If WebGL or the Three.js module is unavailable, the CSS fallback stays in place.
   The arcs are schematic. They do not show vessel routes, live data or shipment volumes. */
(function () {
  'use strict';

  var el = document.getElementById('globe');
  if (!el || !window.ForceLinkGeo) return;

  var GEO = window.ForceLinkGeo;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

  var COLORS = {
    navy: 0x0e305d,
    blue: 0x1a4a8a,
    gold: 0xd6a72c
  };

  var ROTATION_SPEED = 0.07; // radians per second (about one turn every 90 s)
  var SPHERE_POINTS = 1100;
  var ARC_SEGMENTS = 72;
  var PULSE_SPEED = 0.16;    // progress per second along each arc

  var state = {
    renderer: null,
    scene: null,
    camera: null,
    group: null,
    disposables: [],
    arcs: [],           // { points, pulse, offset }
    frameId: null,
    running: false,
    visible: true,
    lastTime: 0,
    observers: [],
    onPageHide: null
  };

  function hasWebGL() {
    try {
      var c = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
    } catch (err) {
      return false;
    }
  }

  if (!hasWebGL()) return;

  function track(obj) {
    state.disposables.push(obj);
    return obj;
  }

  function sizeOf() {
    var rect = el.getBoundingClientRect();
    return { w: Math.max(1, Math.round(rect.width)), h: Math.max(1, Math.round(rect.height)) };
  }

  function makeGlowTexture(THREE) {
    var size = 64;
    var canvas = document.createElement('canvas');
    canvas.width = canvas.height = size;
    var ctx = canvas.getContext('2d');
    var g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.25, 'rgba(255,255,255,0.55)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, size, size);
    var tex = new THREE.CanvasTexture(canvas);
    track(tex);
    return tex;
  }

  function build(THREE) {
    var s = sizeOf();
    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(32, s.w / s.h, 0.1, 100);
    camera.position.z = 3.4;

    var renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(s.w, s.h, false);
    renderer.domElement.setAttribute('aria-hidden', 'true');
    el.appendChild(renderer.domElement);

    var group = new THREE.Group();
    group.rotation.x = 0.32;   // gentle tilt so the arcs read in three dimensions
    scene.add(group);

    // 1. Dotted sphere (the existing visual language), same coordinate convention as the geo module.
    var positions = new Float32Array(SPHERE_POINTS * 3);
    var golden = Math.PI * (3 - Math.sqrt(5));
    for (var i = 0; i < SPHERE_POINTS; i++) {
      var y = 1 - (i / (SPHERE_POINTS - 1)) * 2;
      var radius = Math.sqrt(1 - y * y);
      var theta = golden * i;
      var v = { x: Math.cos(theta) * radius, y: y, z: Math.sin(theta) * radius };
      positions[i * 3] = v.x;
      positions[i * 3 + 1] = v.y;
      positions[i * 3 + 2] = v.z;
    }
    var dotGeo = track(new THREE.BufferGeometry());
    dotGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    var dotMat = track(new THREE.PointsMaterial({
      color: COLORS.navy, size: 0.02, transparent: true, opacity: 0.8, depthWrite: false
    }));
    group.add(new THREE.Points(dotGeo, dotMat));

    // 2. Invisible occluder: hides arcs and markers on the far side of the globe.
    var occGeo = track(new THREE.SphereGeometry(0.985, 48, 32));
    var occMat = track(new THREE.MeshBasicMaterial({ colorWrite: false }));
    var occluder = new THREE.Mesh(occGeo, occMat);
    occluder.renderOrder = -1;
    group.add(occluder);

    var glow = makeGlowTexture(THREE);

    // 3. Arcs + pulses.
    var arcMat = track(new THREE.LineBasicMaterial({
      color: COLORS.blue, transparent: true, opacity: 0.42, depthWrite: false
    }));
    var pulseMat = track(new THREE.SpriteMaterial({
      map: glow, color: COLORS.gold, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending
    }));

    var arcs = [];
    GEO.MARKETS.forEach(function (market, idx) {
      var pts = GEO.arcPoints(GEO.BASE, market, { radius: 1, lift: 0.26, segments: ARC_SEGMENTS });
      var flat = new Float32Array(pts.length * 3);
      pts.forEach(function (p, k) { flat[k * 3] = p.x; flat[k * 3 + 1] = p.y; flat[k * 3 + 2] = p.z; });
      var g = track(new THREE.BufferGeometry());
      g.setAttribute('position', new THREE.BufferAttribute(flat, 3));
      group.add(new THREE.Line(g, arcMat));

      var pulse = new THREE.Sprite(pulseMat);
      pulse.scale.setScalar(0.07);
      group.add(pulse);

      arcs.push({ points: pts, pulse: pulse, offset: idx / GEO.MARKETS.length });
    });

    // 4. Markers. Dubai is gold and larger; destinations are navy with a soft halo.
    function addMarker(lat, lon, colour, halo, coreRadius) {
      var p = GEO.latLonToVec(lat, lon, 1.012);
      var core = new THREE.Mesh(
        track(new THREE.SphereGeometry(coreRadius, 16, 12)),
        track(new THREE.MeshBasicMaterial({ color: colour }))
      );
      core.position.set(p.x, p.y, p.z);
      group.add(core);
      var sprite = new THREE.Sprite(track(new THREE.SpriteMaterial({
        map: glow, color: halo, transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending
      })));
      sprite.position.set(p.x, p.y, p.z);
      sprite.scale.setScalar(coreRadius * 9);
      group.add(sprite);
    }
    addMarker(GEO.BASE.lat, GEO.BASE.lon, COLORS.gold, COLORS.gold, 0.034);
    GEO.MARKETS.forEach(function (m) { addMarker(m.lat, m.lon, COLORS.navy, COLORS.blue, 0.024); });

    state.renderer = renderer;
    state.scene = scene;
    state.camera = camera;
    state.group = group;
    state.arcs = arcs;
    state.occluder = occluder;

    el.classList.add('is-3d');
    el.dataset.ready = 'true';

    var tmp = { x: 0, y: 0, z: 0 };
    state.render = function (elapsed) {
      group.rotation.y = elapsed * ROTATION_SPEED;
      for (var k = 0; k < arcs.length; k++) {
        var a = arcs[k];
        var progress = ((elapsed * PULSE_SPEED) + a.offset) % 1;
        GEO.pointAlong(a.points, progress, tmp);
        a.pulse.position.set(tmp.x, tmp.y, tmp.z);
        // fade pulses in and out at the ends of the arc
        a.pulse.material.opacity = Math.sin(Math.PI * progress) * 0.9;
      }
      renderer.render(scene, camera);
    };

    state.render(0);

    if ('ResizeObserver' in window) {
      var ro = new ResizeObserver(function () {
        if (!state.renderer) return;
        var next = sizeOf();
        camera.aspect = next.w / next.h;
        camera.updateProjectionMatrix();
        renderer.setSize(next.w, next.h, false);
        state.render(state.elapsed || 0);
      });
      ro.observe(el);
      state.observers.push(ro);
    }

    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          state.visible = entry.isIntersecting;
          if (entry.isIntersecting) start(); else stop();
        });
      }, { threshold: 0 });
      io.observe(el);
      state.observers.push(io);
    }

    if (reduceMotion) {
      // Stable, static composition: render once, no loop.
      state.render(0);
    } else {
      start();
    }

    state.onPageHide = dispose;
    window.addEventListener('pagehide', state.onPageHide);
  }

  function loop(now) {
    if (!state.running) return;
    var dt = state.lastTime ? Math.min((now - state.lastTime) / 1000, 0.05) : 0;
    state.lastTime = now;
    state.elapsed = (state.elapsed || 0) + dt;
    state.render(state.elapsed);
    state.frameId = window.requestAnimationFrame(loop);
  }

  function start() {
    if (state.running || reduceMotion || !state.renderer) return;
    state.running = true;
    state.lastTime = 0;
    state.frameId = window.requestAnimationFrame(loop);
  }

  function stop() {
    state.running = false;
    if (state.frameId) window.cancelAnimationFrame(state.frameId);
    state.frameId = null;
  }

  function dispose() {
    stop();
    state.observers.forEach(function (o) { if (o.disconnect) o.disconnect(); });
    state.observers = [];
    if (state.onPageHide) window.removeEventListener('pagehide', state.onPageHide);
    state.disposables.forEach(function (d) { if (d && d.dispose) d.dispose(); });
    state.disposables = [];
    if (state.renderer) {
      state.renderer.dispose();
      if (state.renderer.domElement && state.renderer.domElement.parentNode) {
        state.renderer.domElement.parentNode.removeChild(state.renderer.domElement);
      }
      state.renderer = null;
    }
    el.classList.remove('is-3d');
    el.dataset.ready = 'false';
  }

  import(THREE_URL)
    .then(function (THREE) { build(THREE); })
    .catch(function () {
      // CDN or WebGL failure: keep the CSS fallback; the rest of the page is unaffected.
      dispose();
    });
})();
