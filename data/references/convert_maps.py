"""Convert the selected upstream map data without executing upstream code."""

import argparse
import ast
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ACHRAF_COMMIT = "898188ed31cf31d4ce4c39fec3e3846ed037eee9"
FRANK_COMMIT = "775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562"
MAPS = {
    "fragile_01": ("achraf", "level3", "medium"),
    "fragile_02": ("achraf", "level7", "hard"),
    "soft_toggle_01": ("achraf", "level4", "medium"),
    "soft_toggle_02": ("achraf", "level6", "hard"),
    "heavy_01": ("achraf", "level5", "medium"),
    "heavy_02": ("achraf", "level10", "hard"),
    "bridge_01": ("frank", "levelub", "medium"),
    "permanent_open_01": ("frank", "levelsc", "hard"),
    "permanent_close_01": ("frank", "leveldw", "medium"),
    "split_merge_01": ("frank", "levelss", "medium"),
    "split_merge_02": ("frank", "levelre", "hard"),
    "combined_01": ("frank", "levelht", "hard"),
    "combined_02": ("frank", "leveltb", "hard"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_frank(text):
    """Accept only empty-list assignments and append calls with literal data."""
    levels = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign):
            require(len(node.targets) == 1 and isinstance(node.targets[0], ast.Name),
                    "source: expected one level name")
            name = node.targets[0].id
            require(name.startswith("level") and name not in levels
                    and ast.literal_eval(node.value) == [], "source: invalid level declaration")
            levels[name] = []
        else:
            require(isinstance(node, ast.Expr) and isinstance(node.value, ast.Call),
                    "source: only literal append calls are accepted")
            call = node.value
            require(isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name)
                    and call.func.attr == "append" and len(call.args) == 1
                    and not call.keywords and call.func.value.id in levels,
                    "source: invalid append call")
            levels[call.func.value.id].append(ast.literal_eval(call.args[0]))
    return levels


def convert_achraf(text):
    rows = text.splitlines()
    require(bool(rows) and any(rows), "source: empty map")
    cols = max(map(len, rows))
    codes = [row.ljust(cols, ".") for row in rows]
    tiles = {".": "void", "-": "void", "F": "floor", "S": "floor",
             "T": "goal", "O": "fragile"}
    bridge_cells, switches, starts = {}, [], []
    grid = []
    for r, row in enumerate(codes):
        grid.append([])
        for c, code in enumerate(row):
            cell = [r, c]
            if code == "S":
                starts.append(cell)
            if code in tiles:
                tile = tiles[code]
            elif "a" <= code <= "z":
                tile = "bridge"
                bridge_cells.setdefault(code, []).append(cell)
            elif "A" <= code <= "Z" or "0" <= code <= "9":
                tile = "heavy" if code.isdigit() else "soft"
                target = chr(ord("a") + int(code)) if code.isdigit() else code.lower()
                switches.append((cell, tile, target))
            else:
                raise ValueError(f"source[{r}][{c}]: unknown tile {code!r}")
            grid[-1].append(tile)
    require(len(starts) == 1, "source: expected one start")
    require(sum(row.count("goal") for row in grid) == 1, "source: expected one goal")
    ids = {code: f"b{i:02}" for i, code in enumerate(sorted(bridge_cells), 1)}
    bridges = [{"id": ids[code], "cells": bridge_cells[code], "initial_open": False}
               for code in sorted(ids)]
    result = []
    for i, (cell, tile, target) in enumerate(switches, 1):
        require(target in ids, f"source: switch at {cell} targets missing bridge {target}")
        result.append({"id": f"s{i:02}", "cell": cell, "type": tile,
                       "effect": {"mode": "toggle", "targets": [ids[target]]}})
    return grid, starts[0], bridges, result


def convert_frank(level):
    require(isinstance(level, list) and len(level) in (12, 13), "source: invalid level fields")
    rows, start, effects = level[:10], level[10], level[11]
    splits = level[12] if len(level) == 13 else {}
    require(all(isinstance(row, str) and len(row) == 15 for row in rows),
            "source: expected 10 rows of 15 tiles")
    tiles = {" ": "void", "b": "floor", "e": "goal", "f": "fragile",
             "s": "soft", "h": "heavy", "v": "split",
             "l": "bridge", "r": "bridge", "k": "bridge", "q": "bridge"}
    require(all(code in tiles for row in rows for code in row), "source: unknown tile")
    grid = [[tiles[code] for code in row] for row in rows]
    require(isinstance(start, list) and len(start) == 2
            and all(type(v) is int for v in start)
            and 0 <= start[0] < 15 and 0 <= start[1] < 10
            and grid[start[1]][start[0]] == "floor", "source: invalid start")
    require(sum(row.count("goal") for row in grid) == 1, "source: expected one goal")
    require(isinstance(effects, dict) and isinstance(splits, dict), "source: invalid switch tables")
    buttons = [(r, c, tile) for r, row in enumerate(grid) for c, tile in enumerate(row)
               if tile in {"soft", "heavy", "split"}]
    expected_effects = {f"swatch{c}{r}" for r, c, tile in buttons if tile != "split"}
    expected_splits = {f"swatch{c}{r}" for r, c, tile in buttons if tile == "split"}
    require(set(effects) == expected_effects and set(splits) == expected_splits,
            "source: switch metadata does not match grid")
    modes = {}
    impacts = {}
    for key, targets in effects.items():
        require(isinstance(targets, list) and bool(targets), "source: empty switch targets")
        cells = set()
        for target in targets:
            require(isinstance(target, list) and len(target) == 3
                    and all(type(v) is int for v in target[:2]), "source: invalid bridge target")
            x, y, mode = target
            require(0 <= y < 10 and 0 <= x < 15 and grid[y][x] == "bridge",
                    "source: target must be a bridge")
            require(mode in {"onoff", "on", "off"}, "source: unknown effect")
            require((y, x) not in cells, "source: repeated bridge target")
            cells.add((y, x))
            impacts.setdefault((y, x), []).append((key, mode))
        require(len({target[2] for target in targets}) == 1,
                "source: mixed effects cannot be represented by schema v1")
        modes[key] = targets[0][2]
    groups = {}
    for r, row in enumerate(grid):
        for c, tile in enumerate(row):
            if tile == "bridge":
                signature = (rows[r][c] in "kq", tuple(sorted(impacts.get((r, c), []))))
                groups.setdefault(signature, []).append([r, c])
    bridges = [{"id": f"b{i:02}", "cells": cells, "initial_open": signature[0]}
               for i, (signature, cells) in enumerate(groups.items(), 1)]
    switches = []
    for i, (r, c, tile) in enumerate(buttons, 1):
        key = f"swatch{c}{r}"
        switch = {"id": f"s{i:02}", "cell": [r, c], "type": tile}
        if tile == "split":
            value = splits[key]
            require(isinstance(value, list) and len(value) == 4
                    and all(type(v) is int for v in value), "source: invalid split destinations")
            destinations = [[value[1], value[0]], [value[3], value[2]]]
            require(all(0 <= y < 10 and 0 <= x < 15 and grid[y][x] == "floor"
                        for y, x in destinations), "source: split destinations must be floor")
            require(sum(abs(a-b) for a, b in zip(*destinations)) > 1,
                    "source: split destinations must be distinct and nonadjacent")
            switch.update(destinations=destinations, active_destination=0)
        else:
            targets = {(y, x) for x, y, _ in effects[key]}
            ids = [bridge["id"] for bridge in bridges
                   if any(tuple(cell) in targets for cell in bridge["cells"])]
            effect = {"mode": "toggle" if modes[key] == "onoff" else "permanent", "targets": ids}
            if modes[key] != "onoff":
                effect["open"] = modes[key] == "on"
            switch["effect"] = effect
        switches.append(switch)
    return grid, [start[1], start[0]], bridges, switches


def convert(map_id):
    source, level, difficulty = MAPS[map_id]
    if source == "achraf":
        text = (HERE / "map_sources" / f"achraf_{level}.txt").read_text(encoding="utf-8")
        grid, start, bridges, switches = convert_achraf(text)
        reference = f"https://github.com/AchrafMez/bloxorz/blob/{ACHRAF_COMMIT}/levels/{level}.txt"
    else:
        text = (HERE / "map_sources/frank_selected.txt").read_text(encoding="utf-8")
        grid, start, bridges, switches = convert_frank(read_frank(text)[level])
        reference = f"https://github.com/FrankBuss/bloxorz/blob/{FRANK_COMMIT}/Vide/levels.py"
    return {"schema_version": 1, "id": map_id, "name": f"{map_id.replace('_', ' ').title()} ({level})",
            "difficulty": difficulty, "rows": len(grid), "cols": len(grid[0]), "grid": grid,
            "start": start, "bridges": bridges, "switches": switches,
            "source": {"kind": "adapted", "reference": reference,
                       "conversion_notes": f"data/references/{source}-map-conversion.md"}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_id", choices=MAPS)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/maps/drafts")
    args = parser.parse_args()
    data = convert(args.map_id)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / f"{args.map_id}.json"
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(output)
