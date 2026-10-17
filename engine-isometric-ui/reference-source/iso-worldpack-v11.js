(function (root) {
  "use strict";

  const PACK_KEYS = ["schemaVersion", "id", "baseWorldVersion", "kind", "risk", "status", "kitVersion", "worldBand", "backgroundAssetId", "cell", "quest", "assets", "balance", "provenance", "validation"];
  const CELL_KEYS = ["id", "title", "width", "height", "entry", "exits", "blocked", "tiles", "heights", "entities"];
  const CONNECTOR_KEYS = ["id", "side", "x", "y", "targetCellId"];
  const ENTITY_KEYS = ["id", "type", "x", "y", "z", "orientation", "state", "assetId", "label", "interactionId", "blocking", "zBias", "renderLayer", "assemblyId"];
  const ASSET_KEYS = ["assetId", "source", "runtimeClass", "subject", "footprint", "targetSize", "generationPrompt", "sourceAsset"];
  const BALANCE_KEYS = ["rewardItems", "trustDeltaMax"];
  const PROVENANCE_KEYS = ["promptVersion", "model", "parentAssetIds", "createdAt", "contentHash"];
  const VALIDATION_KEYS = ["status", "checks"];
  const STATUSES = ["draft", "generating", "validating", "staged", "awaiting_approval", "approved", "active", "rolled_back", "rejected", "failed"];
  const LAYERS = ["terrain_face", "terrain_top", "terrain_overlay", "world_object", "overhead", "effect_overlay"];

  const validId = (value) => typeof value === "string" && /^[a-z0-9][a-z0-9_-]{2,63}$/.test(value);
  const validPoint = (value) => value && Number.isInteger(value.x) && Number.isInteger(value.y) && value.x >= 0 && value.y >= 0 && value.x < 12 && value.y < 12;
  const key = (point) => point.x + "," + point.y;

  function exact(value, keys, path, errors) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      errors.push(path + ":OBJECT_REQUIRED");
      return false;
    }
    Object.keys(value).filter((name) => !keys.includes(name)).forEach((name) => errors.push(path + "." + name + ":UNKNOWN_FIELD"));
    keys.filter((name) => !(name in value)).forEach((name) => errors.push(path + "." + name + ":REQUIRED"));
    return true;
  }

  function matrix12(matrix, predicate) {
    return Array.isArray(matrix) && matrix.length === 12
      && matrix.every((row) => Array.isArray(row) && row.length === 12 && row.every(predicate));
  }

  function libraryIndex(library) {
    const index = new Map();
    (library && library.promotedAssets || []).forEach((asset) => index.set(asset.assetId, asset));
    (library && library.runtimeAssets || []).forEach((asset) => index.set(asset.assetId, asset));
    return index;
  }

  function validateConnector(connector, path, errors) {
    if (!exact(connector, CONNECTOR_KEYS, path, errors)) return;
    if (!validId(connector.id) || !validPoint(connector)) errors.push(path + ":INVALID");
    const sides = ["north", "east", "south", "west", "up", "down"];
    if (!sides.includes(connector.side)) errors.push(path + ".side:INVALID");
    const onSide = connector.side === "north" ? connector.y === 0
      : connector.side === "south" ? connector.y === 11
        : connector.side === "west" ? connector.x === 0
          : connector.side === "east" ? connector.x === 11
            : true;
    if (!onSide) errors.push(path + ":NOT_ON_SIDE");
    if (connector.targetCellId !== null && !validId(connector.targetCellId)) errors.push(path + ".targetCellId:INVALID");
  }

  function derivedBlocked(cell) {
    const blocked = new Set();
    cell.tiles.forEach((row, y) => row.forEach((tile, x) => {
      if (tile === "egv1_surface_water") blocked.add(x + "," + y);
    }));
    cell.entities.filter((entity) => entity.blocking).forEach((entity) => blocked.add(key(entity)));
    return blocked;
  }

  function reachable(cell, start, goal) {
    const blocked = new Set(cell.blocked);
    const stairs = new Set(
      cell.entities.filter((entity) => /structure_stairs_[xy]$/.test(entity.assetId)).map(key)
    );
    if (!validPoint(start) || !validPoint(goal) || blocked.has(key(start)) || blocked.has(key(goal))) return false;
    const queue = [start];
    const seen = new Set([key(start)]);
    const moves = [[1, 0], [-1, 0], [0, 1], [0, -1]];
    while (queue.length) {
      const current = queue.shift();
      if (key(current) === key(goal)) return true;
      for (const move of moves) {
        const next = { x: current.x + move[0], y: current.y + move[1] };
        if (!validPoint(next) || blocked.has(key(next)) || seen.has(key(next))) continue;
        const delta = Math.abs(cell.heights[next.y][next.x] - cell.heights[current.y][current.x]);
        if (delta > 0 && !(delta === 1 && (stairs.has(key(current)) || stairs.has(key(next))))) continue;
        seen.add(key(next));
        queue.push(next);
      }
    }
    return false;
  }

  function validateAssetBrief(asset, path, errors, knownAssets, specialAssets) {
    if (!exact(asset, ASSET_KEYS, path, errors)) return;
    if (!validId(asset.assetId) || specialAssets.has(asset.assetId)) errors.push(path + ":INVALID");
    if (knownAssets.has(asset.assetId)) errors.push(path + ":REDUNDANT_LIBRARY_ASSET");
    if (!["generate", "reuse_approved"].includes(asset.source)) errors.push(path + ".source:INVALID");
    if (!["character", "interactable", "pickup"].includes(asset.runtimeClass)) errors.push(path + ".runtimeClass:INVALID");
    if (!validPoint(asset.footprint) || !Number.isInteger(asset.targetSize) || asset.targetSize < 42 || asset.targetSize > 180) errors.push(path + ":INVALID_SIZE");
    if (typeof asset.generationPrompt !== "string" || !asset.generationPrompt || /arcanum|fallout|heroes\s*iii/i.test(asset.generationPrompt)) errors.push(path + ".generationPrompt:INVALID");
    specialAssets.add(asset.assetId);
  }

  function validate(pack, knownItems, library) {
    const errors = [];
    if (!exact(pack, PACK_KEYS, "pack", errors)) return { ok: false, errors };
    if (pack.schemaVersion !== "1.1" || pack.kitVersion !== "emberglass-iso-kit-v1"
      || !validId(pack.id) || !["decor", "minor_event", "quest_cell", "city_cell"].includes(pack.kind)
      || !["low", "approval", "blocked"].includes(pack.risk) || !STATUSES.includes(pack.status)
      || !["ground", "highland", "sky"].includes(pack.worldBand)) errors.push("pack:INVALID_HEADER");
    if (typeof pack.baseWorldVersion !== "string" || !pack.baseWorldVersion) errors.push("pack.baseWorldVersion:REQUIRED");

    const knownAssets = libraryIndex(library);
    if (!knownAssets.size) errors.push("pack:ASSET_LIBRARY_MISSING");
    if (!knownAssets.has(pack.backgroundAssetId)) errors.push("pack.backgroundAssetId:UNKNOWN_ASSET");
    const specialAssets = new Set();
    if (!Array.isArray(pack.assets) || pack.assets.length > 8) errors.push("pack.assets:COUNT");
    else pack.assets.forEach((asset, index) => validateAssetBrief(asset, "pack.assets[" + index + "]", errors, knownAssets, specialAssets));

    if (exact(pack.cell, CELL_KEYS, "pack.cell", errors)) {
      const cell = pack.cell;
      if (!validId(cell.id) || cell.width !== 12 || cell.height !== 12) errors.push("pack.cell:INVALID_GRID");
      const tilesValid = matrix12(cell.tiles, (tile) => typeof tile === "string");
      const heightsValid = matrix12(cell.heights, (height) => Number.isInteger(height) && height >= 0 && height <= 3);
      if (!tilesValid) errors.push("pack.cell.tiles:EXACT_12X12_REQUIRED");
      if (!heightsValid) errors.push("pack.cell.heights:EXACT_12X12_0_TO_3_REQUIRED");
      if (tilesValid) cell.tiles.flat().forEach((tile, index) => {
        if (!knownAssets.has(tile) || knownAssets.get(tile).kind !== "surface") errors.push("pack.cell.tiles[" + index + "]:UNKNOWN_SURFACE_ASSET");
      });
      validateConnector(cell.entry, "pack.cell.entry", errors);
      if (!Array.isArray(cell.exits) || cell.exits.length < 1 || cell.exits.length > 6) errors.push("pack.cell.exits:COUNT");
      else cell.exits.forEach((connector, index) => validateConnector(connector, "pack.cell.exits[" + index + "]", errors));
      if (!Array.isArray(cell.blocked) || new Set(cell.blocked).size !== cell.blocked.length
        || cell.blocked.some((tile) => !/^(?:[0-9]|1[01]),(?:[0-9]|1[01])$/.test(tile))) errors.push("pack.cell.blocked:INVALID");
      if (!Array.isArray(cell.entities) || cell.entities.length < 1 || cell.entities.length > 96) errors.push("pack.cell.entities:COUNT");
      else {
        const ids = new Set();
        cell.entities.forEach((entity, index) => {
          const path = "pack.cell.entities[" + index + "]";
          if (!exact(entity, ENTITY_KEYS, path, errors)) return;
          if (!validId(entity.id) || ids.has(entity.id) || !["npc", "interactable", "pickup", "decor", "connector"].includes(entity.type)
            || !validPoint(entity) || !Number.isInteger(entity.z) || entity.z < 0 || entity.z > 3
            || !["universal", "x", "y", "north", "east", "south", "west"].includes(entity.orientation)
            || !LAYERS.includes(entity.renderLayer) || (!knownAssets.has(entity.assetId) && !specialAssets.has(entity.assetId))) errors.push(path + ":INVALID");
          if (heightsValid && entity.z < cell.heights[entity.y][entity.x]) errors.push(path + ".z:BELOW_TERRAIN");
          if (entity.interactionId !== null && !validId(entity.interactionId)) errors.push(path + ".interactionId:INVALID");
          ids.add(entity.id);
        });
      }
      if (tilesValid && Array.isArray(cell.entities) && Array.isArray(cell.blocked)) {
        const expected = derivedBlocked(cell);
        const actual = new Set(cell.blocked);
        Array.from(expected).filter((tile) => !actual.has(tile)).forEach((tile) => errors.push("pack.cell.blocked:" + tile + ":MISSING_DERIVED_BLOCK"));
        Array.from(actual).filter((tile) => !expected.has(tile)).forEach((tile) => errors.push("pack.cell.blocked:" + tile + ":UNEXPLAINED_BLOCK"));
      }
      if (!errors.length) {
        cell.exits.forEach((point, index) => {
          if (!reachable(cell, cell.entry, point)) errors.push("pack.cell.reachability[" + index + "]:UNREACHABLE");
        });
      }
    }

    if (pack.quest !== null && (!pack.quest || !Array.isArray(pack.quest.steps))) errors.push("pack.quest:INVALID");
    if (pack.quest === null && ["quest_cell", "city_cell"].includes(pack.kind)) errors.push("pack.quest:REQUIRED");
    if (exact(pack.balance, BALANCE_KEYS, "pack.balance", errors)
      && (!Number.isInteger(pack.balance.rewardItems) || pack.balance.rewardItems < 0 || pack.balance.rewardItems > 4
        || !Number.isInteger(pack.balance.trustDeltaMax) || pack.balance.trustDeltaMax < 0 || pack.balance.trustDeltaMax > 2)) errors.push("pack.balance:INVALID");
    if (exact(pack.provenance, PROVENANCE_KEYS, "pack.provenance", errors)
      && (!Array.isArray(pack.provenance.parentAssetIds) || Number.isNaN(Date.parse(pack.provenance.createdAt)))) errors.push("pack.provenance:INVALID");
    if (exact(pack.validation, VALIDATION_KEYS, "pack.validation", errors)
      && (!["pending", "pass", "fail"].includes(pack.validation.status) || !Array.isArray(pack.validation.checks))) errors.push("pack.validation:INVALID");
    return { ok: errors.length === 0, errors };
  }

  const api = { validate, reachable, derivedBlocked, libraryIndex };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.EmberIsoWorldPackV11 = api;
})(typeof window !== "undefined" ? window : globalThis);
