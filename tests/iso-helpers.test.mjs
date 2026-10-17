import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const context = vm.createContext({ module: { exports: {} } });
vm.runInContext(readFileSync(new URL('../engine-isometric-ui/reference-source/iso-kit-renderer.js', import.meta.url), 'utf8'), context);
const iso = context.module.exports;

test('isometric projection round-trips coordinates across height, origin and scale', () => {
  for (const [x, y, z, scale] of [[0, 0, 0, 1], [4, 9, 3, 0.5], [-2, 7, 1, 1.75]]) {
    const origin = { x: 413, y: -29 };
    const p = iso.worldToScreen(x, y, z, scale, origin);
    const result = iso.screenToWorld(p.x, p.y, z, scale, origin);
    assert.ok(Math.abs(result.x - x) < 1e-9 && Math.abs(result.y - y) < 1e-9);
    if (z) assert.notEqual(iso.screenToWorld(p.x, p.y, 0, scale, origin).x, x);
  }
});

test('tile picking finds the projected cell and rejects points outside the map', () => {
  const cell = { heights: Array.from({ length: 12 }, () => Array(12).fill(0)) };
  const origin = { x: 300, y: 100 };
  const p = iso.worldToScreen(4, 6, 0, 0.75, origin);
  assert.equal(JSON.stringify(iso.clickTarget(p.x, p.y, cell, 0.75, origin)), '{"x":4,"y":6,"z":0}');
  assert.equal(iso.clickTarget(-10000, -10000, cell, 0.75, origin), null);
});
