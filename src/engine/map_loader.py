"""Strict schema-v1 loader for basic and advanced Bloxorz maps."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

Coordinate = tuple[int, int]
_BASIC_TILES = {"void", "floor", "goal", "fragile"}
_ADVANCED_TILES = {"soft", "heavy", "split", "bridge"}
_REQUIRED_KEYS = {
    "schema_version", "id", "name", "difficulty", "rows", "cols", "grid",
    "start", "bridges", "switches", "source",
}
_OPTIONAL_KEYS = {"expected_solvable"}


@dataclass(frozen=True)
class Bridge:
    id: str
    cells: tuple[Coordinate, ...]
    initial_open: bool


@dataclass(frozen=True)
class Switch:
    id: str
    cell: Coordinate
    type: str
    effect_mode: str | None = None
    targets: tuple[str, ...] = ()
    open: bool | None = None
    destinations: tuple[Coordinate, ...] = ()
    active_destination: int | None = None


@dataclass(frozen=True)
class GameMap:
    id: str
    name: str
    difficulty: str
    rows: int
    cols: int
    grid: tuple[tuple[str, ...], ...]
    start: Coordinate
    goal: Coordinate
    expected_solvable: bool | None = None

    bridges: tuple[Bridge, ...] = ()
    switches: tuple[Switch, ...] = ()

    @property
    def bridge_ids(self) -> tuple[str, ...]:
        return tuple(bridge.id for bridge in self.bridges)

    def tile_at(self, cell: Coordinate) -> str:
        row, col = cell
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return "void"
        return self.grid[row][col]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _coordinate(value: Any, path: str, rows: int, cols: int) -> Coordinate:
    _require(isinstance(value, list) and len(value) == 2
             and all(type(part) is int for part in value),
             f"{path}: expected [row, col] with integer coordinates")
    row, col = value
    _require(0 <= row < rows and 0 <= col < cols,
             f"{path}: coordinate {value} is outside the map")
    return row, col


def parse_map(data: Any) -> GameMap:
    """Validate a decoded map object and return immutable map data."""
    _require(isinstance(data, dict), "map: expected a JSON object")
    missing = _REQUIRED_KEYS - data.keys()
    extra = data.keys() - _REQUIRED_KEYS - _OPTIONAL_KEYS
    _require(not missing, f"map: missing required field(s): {', '.join(sorted(missing))}")
    _require(not extra, f"map: unknown field(s): {', '.join(sorted(extra))}")
    _require(type(data["schema_version"]) is int and data["schema_version"] == 1,
             "schema_version: only integer version 1 is supported")
    for key in ("id", "name"):
        _require(isinstance(data[key], str) and bool(data[key].strip()),
                 f"{key}: expected a non-empty string")
    _require(isinstance(data["difficulty"], str)
             and data["difficulty"] in {"easy", "medium", "hard"},
             'difficulty: expected "easy", "medium", or "hard"')
    rows, cols = data["rows"], data["cols"]
    _require(type(rows) is int and rows > 0, "rows: expected a positive integer")
    _require(type(cols) is int and cols > 0, "cols: expected a positive integer")
    grid_data = data["grid"]
    _require(isinstance(grid_data, list) and len(grid_data) == rows,
             f"grid: expected exactly {rows} rows")
    grid: list[tuple[str, ...]] = []
    goals: list[Coordinate] = []
    for row_index, row in enumerate(grid_data):
        _require(isinstance(row, list) and len(row) == cols,
                 f"grid[{row_index}]: expected exactly {cols} cells")
        validated_row: list[str] = []
        for col_index, tile in enumerate(row):
            _require(isinstance(tile, str),
                     f"grid[{row_index}][{col_index}]: expected a tile string")
            _require(tile in _BASIC_TILES | _ADVANCED_TILES,
                     f"grid[{row_index}][{col_index}]: unknown tile {tile!r}")
            if tile == "goal":
                goals.append((row_index, col_index))
            validated_row.append(tile)
        grid.append(tuple(validated_row))
    _require(len(goals) == 1, f"grid: expected exactly one goal, found {len(goals)}")
    start = _coordinate(data["start"], "start", rows, cols)
    _require(grid[start[0]][start[1]] == "floor",
             f"start: coordinate {list(start)} must be on floor")
    _require(isinstance(data["bridges"], list), "bridges: expected an array")
    _require(isinstance(data["switches"], list), "switches: expected an array")
    bridges, switches = _advanced(data, grid, rows, cols)
    source = data["source"]
    _require(isinstance(source, dict), "source: expected an object")
    kind = source.get("kind")
    _require(isinstance(kind, str) and kind in {"original", "adapted"},
             'source.kind: expected "original" or "adapted"')
    _require(isinstance(source.get("reference"), str)
             and bool(source["reference"].strip()),
             "source.reference: expected a non-empty string")
    if kind == "original":
        _require(set(source) == {"kind", "reference"},
                 "source: original source accepts only kind and reference")
    else:
        _require(set(source) == {"kind", "reference", "conversion_notes"},
                 "source: adapted source requires conversion_notes and no other fields")
        _require(isinstance(source["conversion_notes"], str)
                 and bool(source["conversion_notes"].strip()),
                 "source.conversion_notes: expected a non-empty string")
    expected = data.get("expected_solvable")
    _require("expected_solvable" not in data or type(expected) is bool,
             "expected_solvable: expected true, false, or omission")
    return GameMap(data["id"], data["name"], data["difficulty"], rows, cols,
                   tuple(grid), start, goals[0], expected, bridges, switches)


def _keys(obj, required, path, optional=()):
    _require(isinstance(obj, dict), f"{path}: expected an object")
    missing = set(required) - obj.keys()
    extra = obj.keys() - set(required) - set(optional)
    _require(not missing, f"{path}: missing field(s) {sorted(missing)}")
    _require(not extra, f"{path}: unknown field(s) {sorted(extra)}")


def _identifier(value, path):
    _require(isinstance(value, str) and bool(value.strip()),
             f"{path}: expected a non-empty string")
    return value


def _advanced(data, grid, rows, cols):
    bridges, switches = [], []
    ids, bridge_cells = set(), set()
    for i, item in enumerate(data["bridges"]):
        path = f"bridges[{i}]"
        _keys(item, ("id", "cells", "initial_open"), path)
        ident = _identifier(item["id"], path + ".id")
        _require(ident not in ids, path + ".id: duplicate bridge ID")
        ids.add(ident)
        _require(type(item["initial_open"]) is bool, path + ".initial_open: expected bool")
        _require(isinstance(item["cells"], list) and bool(item["cells"]),
                 path + ".cells: expected non-empty array")
        cells = []
        for j, value in enumerate(item["cells"]):
            at = f"{path}.cells[{j}]"
            cell = _coordinate(value, at, rows, cols)
            _require(grid[cell[0]][cell[1]] == "bridge", at + ": not a bridge tile")
            _require(cell not in bridge_cells, at + ": bridge tile assigned more than once")
            bridge_cells.add(cell)
            cells.append(cell)
        bridges.append(Bridge(ident, tuple(sorted(cells)), item["initial_open"]))
    all_bridge_cells = {(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == "bridge"}
    _require(all_bridge_cells == bridge_cells, "bridges: every bridge tile must have exactly one group")
    switch_ids, switch_cells = set(), set()
    for i, item in enumerate(data["switches"]):
        path = f"switches[{i}]"
        _require(isinstance(item, dict), path + ": expected object")
        typ = item.get("type")
        _require(isinstance(typ, str) and typ in {"soft", "heavy", "split"}, path + ".type: invalid switch type")
        required = ("id", "cell", "type", "destinations", "active_destination") if typ == "split" else ("id", "cell", "type", "effect")
        _keys(item, required, path)
        ident = _identifier(item["id"], path + ".id")
        _require(ident not in switch_ids, path + ".id: duplicate switch ID")
        switch_ids.add(ident)
        cell = _coordinate(item["cell"], path + ".cell", rows, cols)
        _require(grid[cell[0]][cell[1]] == typ, path + ".cell: tile does not match type")
        _require(cell not in switch_cells, path + ".cell: duplicate switch cell")
        switch_cells.add(cell)
        if typ == "split":
            dest = item["destinations"]
            _require(isinstance(dest, list) and len(dest) == 2, path + ".destinations: expected two coordinates")
            dest = tuple(_coordinate(v, f"{path}.destinations[{j}]", rows, cols) for j, v in enumerate(dest))
            _require(dest[0] != dest[1], path + ".destinations: coordinates must differ")
            _require(all(grid[r][c] == "floor" for r, c in dest), path + ".destinations: both must be floor")
            _require(sum(abs(x-y) for x,y in zip(*dest)) != 1, path + ".destinations: cubes must not be adjacent")
            active = item["active_destination"]
            _require(type(active) is int and active in (0, 1), path + ".active_destination: expected integer 0 or 1")
            switches.append(Switch(ident, cell, typ, destinations=dest, active_destination=active))
        else:
            effect = item["effect"]
            _require(isinstance(effect, dict), path + ".effect: expected object")
            mode = effect.get("mode")
            _require(isinstance(mode, str) and mode in {"toggle", "permanent"}, path + ".effect.mode: invalid mode")
            _keys(effect, ("mode", "targets", "open") if mode == "permanent" else ("mode", "targets"), path + ".effect")
            targets = effect["targets"]
            _require(isinstance(targets, list) and bool(targets), path + ".effect.targets: expected non-empty array")
            seen = set()
            for j, target in enumerate(targets):
                _identifier(target, f"{path}.effect.targets[{j}]")
                _require(target in ids, f"{path}.effect.targets[{j}]: unknown bridge {target!r}")
                _require(target not in seen, path + ".effect.targets: duplicate bridge ID")
                seen.add(target)
            opened = effect.get("open")
            if mode == "permanent":
                _require(type(opened) is bool, path + ".effect.open: expected bool")
            switches.append(Switch(ident, cell, typ, mode, tuple(targets), opened))
    all_switch_cells = {(r,c) for r in range(rows) for c in range(cols) if grid[r][c] in {"soft", "heavy", "split"}}
    _require(all_switch_cells == switch_cells, "switches: every switch tile must have exactly one declaration")
    return tuple(sorted(bridges, key=lambda b: b.id)), tuple(sorted(switches, key=lambda s: s.id))


def load_map(path: str | Path) -> GameMap:
    """Read UTF-8 JSON and report malformed JSON or schema errors clearly."""
    map_path = Path(path)
    try:
        with map_path.open("r", encoding="utf-8") as stream:
            data = json.load(stream, parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"Invalid JSON constant {value}")))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{map_path}: invalid JSON at line {exc.lineno}, "
                         f"column {exc.colno}: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"{map_path}: cannot read map: {exc}") from exc
    return parse_map(data)
