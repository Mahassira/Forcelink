/* Decorative particle globe (Three.js). Loaded only on the home page.
   If WebGL or the Three.js module is unavailable, the CSS fallback stays in place
   and nothing else on the page is affected. The globe is decorative and does not
   show locations, markets or shipment routes. */
(function () {
  'use strict';

  var el = document.getElementById('globe');
  if (!el) return;

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

  function hasWebGL() {
    try {
      var c = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
    } catch (err) {
      return false;
    }
  }

  if (!hasWebGL()) return;

  var renderer = null;
  var geometry = null;
  var material = null;
  var frameId = null;
  var running = false;
  var THREE_MOD = null;
  var scene, camera, points;

  function render() {
    renderer.render(scene, camera);
  }

  function loop() {
    if (!running) return;
    points.rotation.y += 0.0014;
    points.rotation.x = 0.25;
    render();
    frameId = window.requestAnimationFrame(loop);
  }

  function start() {
    if (running || reduceMotion) return;
    running = true;
    frameId = window.requestAnimationFrame(loop);
  }

  function stop() {
    running = false;
    if (frameId) window.cancelAnimationFrame(frameId);
    frameId = null;
  }

  function dispose() {
    stop();
    if (geometry) geometry.dispose();
    if (material) material.dispose();
    if (renderer) {
      renderer.dispose();
      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
    }
    renderer = null;
  }

  function sizeOf() {
    var rect = el.getBoundingClientRect();
    return { w: Math.max(1, Math.round(rect.width)), h: Math.max(1, Math.round(rect.height)) };
  }

  function build(THREE) {
    THREE_MOD = THREE;
    var s = sizeOf();
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(35, s.w / s.h, 0.1, 100);
    camera.position.z = 3.3;

    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(s.w, s.h, false);
    renderer.domElement.setAttribute('aria-hidden', 'true');
    el.appendChild(renderer.domElement);

    // Fibonacci sphere: evenly distributed points, cheap to render.
    var N = 1100;
    var positions = new Float32Array(N * 3);
    var golden = Math.PI * (3 - Math.sqrt(5));
    for (var i = 0; i < N; i++) {
      var y = 1 - (i / (N - 1)) * 2;
      var radius = Math.sqrt(1 - y * y);
      var theta = golden * i;
      positions[i * 3] = Math.cos(theta) * radius;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = Math.sin(theta) * radius;
    }
    geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    material = new THREE.PointsMaterial({
      color: 0x0e305d,
      size: 0.022,
      transparent: true,
      opacity: 0.85,
      depthWrite: false
    });
    points = new THREE.Points(geometry, material);
    scene.add(points);

    el.classList.add('is-3d');
    render();

    if ('ResizeObserver' in window) {
      new ResizeObserver(function () {
        if (!renderer) return;
        var next = sizeOf();
        camera.aspect = next.w / next.h;
        camera.updateProjectionMatrix();
        renderer.setSize(next.w, next.h, false);
        render();
      }).observe(el);
    }

    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) start();
          else stop();
        });
      }, { threshold: 0 }).observe(el);
    } else {
      start();
    }

    if (reduceMotion) render();

    window.addEventListener('pagehide', dispose);
  }

  import(THREE_URL)
    .then(function (THREE) { build(THREE); })
    .catch(function () {
      /* Keep the CSS fallback visible; the rest of the page is unaffected. */
      dispose();
    });
})();
