"""Strict JSON loader and validator for the basic Bloxorz milestone."""

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
    """Validate a decoded map object and return immutable basic map data."""
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
    unsupported: list[str] = []
    for row_index, row in enumerate(grid_data):
        _require(isinstance(row, list) and len(row) == cols,
                 f"grid[{row_index}]: expected exactly {cols} cells")
        validated_row: list[str] = []
        for col_index, tile in enumerate(row):
            _require(isinstance(tile, str),
                     f"grid[{row_index}][{col_index}]: expected a tile string")
            _require(tile in _BASIC_TILES | _ADVANCED_TILES,
                     f"grid[{row_index}][{col_index}]: unknown tile {tile!r}")
            if tile in _ADVANCED_TILES:
                unsupported.append(f"{tile}@[{row_index},{col_index}]")
            if tile == "goal":
                goals.append((row_index, col_index))
            validated_row.append(tile)
        grid.append(tuple(validated_row))
    _require(len(goals) == 1, f"grid: expected exactly one goal, found {len(goals)}")
    if unsupported:
        raise ValueError("grid: advanced tiles are not supported in the basic release: "
                         + ", ".join(unsupported))
    start = _coordinate(data["start"], "start", rows, cols)
    _require(grid[start[0]][start[1]] == "floor",
             f"start: coordinate {list(start)} must be on floor")
    _require(isinstance(data["bridges"], list), "bridges: expected an array")
    _require(isinstance(data["switches"], list), "switches: expected an array")
    _require(data["bridges"] == [],
             "bridges: advanced bridge mechanics are not in the basic release")
    _require(data["switches"] == [],
             "switches: advanced switch mechanics are not in the basic release")
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
    _require(expected is None or type(expected) is bool,
             "expected_solvable: expected true, false, or omission")
    return GameMap(data["id"], data["name"], data["difficulty"], rows, cols,
                   tuple(grid), start, goals[0], expected)


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
