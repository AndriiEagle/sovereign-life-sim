(function (root) {
  "use strict";

  const TILE_WIDTH = 128;
  const TILE_HEIGHT = 64;
  const Z_LIFT = 64;
  const SCALES = { mobile: 0.5, desktop: 0.75, zoom: 1 };
  const BITS = [
    { dx: 0, dy: -1, bit: 1 },
    { dx: 1, dy: 0, bit: 2 },
    { dx: 0, dy: 1, bit: 4 },
    { dx: -1, dy: 0, bit: 8 },
  ];
  const LAYERS = {
    terrain_face: 0,
    terrain_top: 1,
    terrain_overlay: 2,
    world_object: 3,
    overhead: 4,
    effect_overlay: 5,
  };
  const state = { manifest: null, atlas: null, runtime: new Map(), masters: new Map(), baseUrl: "" };

  function scaleForViewport(width, zoomed) {
    if (zoomed) return SCALES.zoom;
    return width < 700 ? SCALES.mobile : SCALES.desktop;
  }

  function worldToScreen(worldX, worldY, worldZ, scale, origin) {
    const base = origin || { x: 0, y: 0 };
    return {
      x: base.x + (worldX - worldY) * 64 * scale,
      y: base.y + (worldX + worldY) * 32 * scale - worldZ * 64 * scale,
    };
  }

  function screenToWorld(screenX, screenY, worldZ, scale, origin) {
    const base = origin || { x: 0, y: 0 };
    const localX = screenX - base.x;
    const liftedY = screenY - base.y + worldZ * 64 * scale;
    return {
      x: liftedY / (64 * scale) + localX / (128 * scale),
      y: liftedY / (64 * scale) - localX / (128 * scale),
    };
  }

  function cameraBounds(cell, scale, padding) {
    const margin = padding === undefined ? 128 * scale : padding;
    const points = [];
    for (let y = 0; y < 12; y += 1) {
      for (let x = 0; x < 12; x += 1) points.push(worldToScreen(x, y, cell.heights[y][x], scale));
    }
    return {
      minX: Math.min.apply(null, points.map((point) => point.x)) - margin,
      maxX: Math.max.apply(null, points.map((point) => point.x)) + margin,
      minY: Math.min.apply(null, points.map((point) => point.y)) - margin,
      maxY: Math.max.apply(null, points.map((point) => point.y)) + margin,
    };
  }

  function clickTarget(screenX, screenY, cell, scale, origin) {
    let best = null;
    for (let y = 0; y < 12; y += 1) {
      for (let x = 0; x < 12; x += 1) {
        const point = worldToScreen(x, y, cell.heights[y][x], scale, origin);
        const dx = Math.abs(screenX - point.x) / (64 * scale);
        const dy = Math.abs(screenY - point.y) / (32 * scale);
        const distance = dx + dy;
        const z = cell.heights[y][x];
        if (distance <= 1 && (!best || distance < best.distance - 0.0001 || Math.abs(distance - best.distance) <= 0.0001 && z > best.z)) {
          best = { x, y, z, distance };
        }
      }
    }
    return best && { x: best.x, y: best.y, z: best.z };
  }

  function autotileMask(grid, x, y, matches) {
    let mask = 0;
    for (const edge of BITS) {
      const nx = x + edge.dx;
      const ny = y + edge.dy;
      if (ny >= 0 && ny < grid.length && nx >= 0 && nx < grid[ny].length && matches(grid[ny][nx], nx, ny)) mask |= edge.bit;
    }
    return mask;
  }

  function trimAssetId(profile, mask) {
    return mask === 15 ? "egv1_trim_" + profile : "egv1_trim_" + profile + "_mask_" + String(mask).padStart(2, "0");
  }

  function networkAssetId(family, mask) {
    if (mask === 5) return "egv1_network_" + family + "_y";
    if (mask === 10) return "egv1_network_" + family + "_x";
    if (mask === 15) return "egv1_network_" + family + "_junction";
    return "egv1_network_" + family + "_mask_" + String(mask).padStart(2, "0");
  }

  function indexManifest(manifest) {
    state.runtime = new Map((manifest.runtimeAssets || []).map((asset) => [asset.assetId, asset]));
    state.masters = new Map((manifest.promotedAssets || []).map((asset) => [asset.assetId, asset]));
  }

  function init(manifest, baseUrl) {
    if (!manifest || manifest.kitVersion !== "emberglass-iso-kit-v1") throw new Error("ISO_KIT_MANIFEST_MISSING_OR_WRONG_VERSION");
    if (manifest.promotedAssets.some((asset) => asset.qaStatus !== "promoted" || /scaffold_only/.test(asset.artStatus || ""))) {
      throw new Error("ISO_KIT_SCAFFOLD_OR_UNPROMOTED_ASSET");
    }
    state.manifest = manifest;
    state.baseUrl = (baseUrl || "assets/iso-kit/" + manifest.kitVersion).replace(/\/$/, "");
    indexManifest(manifest);
    if (typeof Image === "undefined") return Promise.resolve(false);
    state.atlas = new Image();
    state.atlas.decoding = "async";
    return new Promise((resolve, reject) => {
      state.atlas.onload = () => resolve(true);
      state.atlas.onerror = () => reject(new Error("ISO_KIT_ATLAS_LOAD_FAILED"));
      state.atlas.src = state.baseUrl + "/" + manifest.atlas.file;
    });
  }

  function setAtlasImageForTest(atlas) {
    state.atlas = atlas;
  }

  function masterFor(runtimeAsset) {
    return state.masters.get(runtimeAsset.masterAssetId || runtimeAsset.assetId);
  }

  function assertAsset(assetId) {
    const runtimeAsset = state.runtime.get(assetId);
    if (!runtimeAsset || !runtimeAsset.frame) throw new Error("ISO_KIT_ASSET_MISSING:" + assetId);
    const master = masterFor(runtimeAsset);
    if (!master) throw new Error("ISO_KIT_METADATA_MISSING:" + assetId);
    return { runtimeAsset, master };
  }

  function assertPackAssets(pack) {
    if (!state.manifest || !state.atlas) throw new Error("ISO_KIT_NOT_READY");
    assertAsset(pack.backgroundAssetId);
    pack.cell.tiles.flat().forEach(assertAsset);
    pack.cell.entities.forEach((item) => assertAsset(item.assetId));
    if (pack.assets.length) throw new Error("ISO_KIT_SPECIAL_ASSET_NOT_PROMOTED");
    return true;
  }

  function drawAsset(ctx, assetId, anchor, scale, alpha) {
    const found = assertAsset(assetId);
    const frame = found.runtimeAsset.frame;
    const pivot = found.master.pivot || { x: 64, y: 96 };
    const oldAlpha = ctx.globalAlpha;
    ctx.globalAlpha = alpha === undefined ? 1 : alpha;
    ctx.drawImage(
      state.atlas,
      frame.x, frame.y, frame.w, frame.h,
      Math.round(anchor.x - pivot.x * scale),
      Math.round(anchor.y - pivot.y * scale),
      Math.round(frame.w * scale),
      Math.round(frame.h * scale)
    );
    ctx.globalAlpha = oldAlpha;
  }

  function terrainTrimProfile(pack) {
    if (pack.worldBand === "sky") return "cloud_floating_island_rim";
    if (pack.cell.id === "machine_yard") return "metal_hull";
    return "rock_cliff";
  }

  function drawBackground(ctx, pack, scale) {
    ctx.fillStyle = pack.worldBand === "sky" ? "#70838a" : "#34312d";
    ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    const positions = pack.worldBand === "sky"
      ? [[0.14, 0.17, 0.55], [0.76, 0.27, 0.42], [0.44, 0.08, 0.35]]
      : [[0.13, 0.12, 0.28], [0.83, 0.16, 0.22]];
    positions.forEach((position) => {
      drawAsset(ctx, pack.backgroundAssetId, { x: ctx.canvas.width * position[0], y: ctx.canvas.height * position[1] }, scale * position[2], 0.5);
    });
  }

  function networkFamily(assetId) {
    const match = /^egv1_network_(road|rail|pipe_cable|fence_railing)_/.exec(assetId);
    return match && match[1];
  }

  function resolvedNetworkAssets(entities) {
    const result = new Map();
    const families = ["road", "rail", "pipe_cable", "fence_railing"];
    for (const family of families) {
      const grid = Array.from({ length: 12 }, () => Array(12).fill(false));
      entities.filter((item) => networkFamily(item.assetId) === family).forEach((item) => { grid[item.y][item.x] = true; });
      entities.filter((item) => networkFamily(item.assetId) === family).forEach((item) => {
        const mask = autotileMask(grid, item.x, item.y, (value) => value === true);
        result.set(item.id, networkAssetId(family, mask));
      });
    }
    return result;
  }

  function render(ctx, pack, player, view) {
    assertPackAssets(pack);
    const options = view || {};
    const scale = options.scale || scaleForViewport(ctx.canvas.width, options.zoomed);
    const origin = options.origin || { x: Math.round(ctx.canvas.width / 2), y: Math.round(82 + 3 * 64 * scale) };
    ctx.imageSmoothingEnabled = false;
    drawBackground(ctx, pack, scale);
    const profile = terrainTrimProfile(pack);

    for (let diagonal = 0; diagonal <= 22; diagonal += 1) {
      for (let x = 0; x < 12; x += 1) {
        const y = diagonal - x;
        if (y < 0 || y >= 12) continue;
        const height = pack.cell.heights[y][x];
        const anchor = worldToScreen(x, y, height, scale, origin);
        if (height > 0) {
          const exposedMask = autotileMask(pack.cell.heights, x, y, (neighborHeight) => neighborHeight < height);
          for (let level = 0; level < height; level += 1) {
            drawAsset(ctx, trimAssetId(profile, exposedMask), { x: anchor.x, y: anchor.y + (level + 1) * Z_LIFT * scale }, scale);
          }
        }
        drawAsset(ctx, pack.cell.tiles[y][x], anchor, scale);
      }
    }

    const networks = resolvedNetworkAssets(pack.cell.entities);
    const sorted = [...pack.cell.entities].sort((left, right) => {
      const layer = (LAYERS[left.renderLayer] || 0) - (LAYERS[right.renderLayer] || 0);
      if (layer) return layer;
      const leftDepth = left.x + left.y + left.z + left.zBias / 64;
      const rightDepth = right.x + right.y + right.z + right.zBias / 64;
      return leftDepth - rightDepth || left.id.localeCompare(right.id);
    });
    sorted.forEach((item) => {
      const assetId = networks.get(item.id) || item.assetId;
      const anchor = worldToScreen(item.x, item.y, item.z, scale, origin);
      const occludesPlayer = item.renderLayer === "overhead" && player
        && Math.abs(item.x - player.x) <= 1 && Math.abs(item.y - player.y) <= 1;
      drawAsset(ctx, assetId, anchor, scale, occludesPlayer ? 0.38 : 1);
    });
    return { scale, origin, bounds: cameraBounds(pack.cell, scale) };
  }

  const api = {
    TILE_WIDTH, TILE_HEIGHT, Z_LIFT, SCALES,
    init, render, drawAsset, worldToScreen, screenToWorld, cameraBounds, clickTarget,
    autotileMask, trimAssetId, networkAssetId, assertPackAssets, scaleForViewport,
    setAtlasImageForTest,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.EmberIsoKitRenderer = api;
})(typeof window !== "undefined" ? window : globalThis);
