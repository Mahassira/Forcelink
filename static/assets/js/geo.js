/* Geographic maths for the market-connections globe. No dependencies.
   Shared by globe.js (rendering) and tests/geo.test.js (verification).

   Coordinate convention (matches three.js SphereGeometry):
     phi   = (90 - lat) in radians, theta = (lon + 180) in radians
     x = -r * sin(phi) * cos(theta)
     y =  r * cos(phi)
     z =  r * sin(phi) * sin(theta)

   All markers and arcs use this one function, so they stay aligned under rotation.
   Positions are representative country-level points for an illustration, not
   verified shipment coordinates, ports or customer locations. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.ForceLinkGeo = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  var DEG = Math.PI / 180;

  var BASE = {
    key: 'dubai',
    label: 'Dubai, UAE',
    role: 'Company base',
    lat: 25.2048,
    lon: 55.2708
  };

  var MARKETS = [
    { key: 'india', label: 'India', lat: 22.9734, lon: 78.6569 },
    { key: 'china', label: 'China', lat: 35.8617, lon: 104.1954 },
    { key: 'malaysia', label: 'Malaysia', lat: 4.2105, lon: 101.9758 },
    { key: 'vietnam', label: 'Vietnam', lat: 14.0583, lon: 108.2772 },
    { key: 'indonesia', label: 'Indonesia', lat: -0.7893, lon: 113.9213 },
    // Europe is a regional designation, represented by a central point.
    { key: 'europe', label: 'Europe (region)', lat: 54.526, lon: 15.2551 }
  ];

  /** Latitude/longitude (degrees) to a point on a sphere of radius r. */
  function latLonToVec(lat, lon, r) {
    var radius = r === undefined ? 1 : r;
    var phi = (90 - lat) * DEG;
    var theta = (lon + 180) * DEG;
    return {
      x: -radius * Math.sin(phi) * Math.cos(theta),
      y: radius * Math.cos(phi),
      z: radius * Math.sin(phi) * Math.sin(theta)
    };
  }

  /** Inverse of latLonToVec. Returns { lat, lon } in degrees. */
  function vecToLatLon(v) {
    var len = Math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
    var lat = Math.asin(v.y / len) / DEG;
    var phi = Math.acos(Math.max(-1, Math.min(1, v.y / len)));
    var sinPhi = Math.sin(phi);
    var theta = Math.atan2(v.z / (len * sinPhi || 1), -v.x / (len * sinPhi || 1));
    var lon = theta / DEG - 180;
    // normalise to [-180, 180)
    lon = ((lon + 540) % 360) - 180;
    return { lat: lat, lon: lon };
  }

  /**
   * Curved arc between two lat/lon points.
   * Interpolates along the great circle (spherical linear interpolation) and lifts
   * the middle of the path above the surface by `lift` (fraction of radius).
   * Returns `segments + 1` points as { x, y, z }.
   */
  function arcPoints(from, to, opts) {
    var o = opts || {};
    var R = o.radius === undefined ? 1 : o.radius;
    var lift = o.lift === undefined ? 0.28 : o.lift;
    var segments = o.segments || 64;

    var a = latLonToVec(from.lat, from.lon, 1);
    var b = latLonToVec(to.lat, to.lon, 1);
    var dot = Math.max(-1, Math.min(1, a.x * b.x + a.y * b.y + a.z * b.z));
    var omega = Math.acos(dot);
    var sinOmega = Math.sin(omega);

    var pts = [];
    for (var i = 0; i <= segments; i++) {
      var t = i / segments;
      var p;
      if (sinOmega < 1e-9) {
        p = { x: a.x, y: a.y, z: a.z };
      } else {
        var wa = Math.sin((1 - t) * omega) / sinOmega;
        var wb = Math.sin(t * omega) / sinOmega;
        p = {
          x: wa * a.x + wb * b.x,
          y: wa * a.y + wb * b.y,
          z: wa * a.z + wb * b.z
        };
      }
      // Smooth lift: zero at both ends, peak at the middle.
      var radius = R * (1 + lift * Math.sin(Math.PI * t));
      var len = Math.sqrt(p.x * p.x + p.y * p.y + p.z * p.z);
      pts.push({
        x: (p.x / len) * radius,
        y: (p.y / len) * radius,
        z: (p.z / len) * radius
      });
    }
    return pts;
  }

  /**
   * Position along a polyline of points at fractional progress p in [0, 1].
   * Linear interpolation between neighbouring points; allocation-free when `out` is given.
   */
  function pointAlong(points, p, out) {
    var o = out || { x: 0, y: 0, z: 0 };
    var f = Math.max(0, Math.min(1, p)) * (points.length - 1);
    var i = Math.floor(f);
    if (i >= points.length - 1) {
      var last = points[points.length - 1];
      o.x = last.x; o.y = last.y; o.z = last.z;
      return o;
    }
    var k = f - i;
    var a = points[i];
    var b = points[i + 1];
    o.x = a.x + (b.x - a.x) * k;
    o.y = a.y + (b.y - a.y) * k;
    o.z = a.z + (b.z - a.z) * k;
    return o;
  }

  return {
    BASE: BASE,
    MARKETS: MARKETS,
    latLonToVec: latLonToVec,
    vecToLatLon: vecToLatLon,
    arcPoints: arcPoints,
    pointAlong: pointAlong
  };
});
