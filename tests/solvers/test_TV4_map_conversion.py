import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from data.references.convert_maps import (
    MAPS, convert, convert_achraf, convert_frank, read_frank,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "data/references/map_sources"
SOURCE_HASHES = {
    "frank_selected.txt": "9fb8af459e8d694ea2f725bd6162f4403a4ef1d0ca9c52667fd88fc53f510cb0",
    "achraf_level3.txt": "7a36a4589fc483222920db929c00d86f1f80ed69a4afe353e1842899b97024e8",
    "achraf_level7.txt": "86e5db7b81ce39d4f6d3973e86a1b95d3190b1adc2f5c0e26cbb0dd4daf75293",
    "achraf_level4.txt": "75687be941975108e25639cf906cba6a4f3adfc8ec3deaeaf1ed0228dcef8dad",
    "achraf_level6.txt": "80a936bcd644fc1fe389d419c004f57e6a7452e758a87d3d094ad57fdf367413",
    "achraf_level5.txt": "f896dfc1ecbee5c17348b90144800c051c469d4307f0a8efa0a3cf0e8a207414",
    "achraf_level10.txt": "de6d0f5542ef8c06990ca8518d92fd28f49e7846d7797ec463fc9ab71918d38d",
}
EXPECTED_IDS = {
    "fragile_01", "fragile_02", "soft_toggle_01", "soft_toggle_02", "heavy_01", "heavy_02",
    "bridge_01", "permanent_open_01", "permanent_close_01", "split_merge_01", "split_merge_02",
    "combined_01", "combined_02",
}


class TestMapConversion(unittest.TestCase):
    def frank_levels(self):
        return read_frank((SOURCES / "frank_selected.txt").read_text(encoding="utf-8"))

    def test_source_bytes_are_pinned(self):
        for name, digest in SOURCE_HASHES.items():
            with self.subTest(source=name):
                self.assertEqual(hashlib.sha256((SOURCES / name).read_bytes()).hexdigest(), digest)

    def test_achraf_real_format_and_padding(self):
        grid, start, bridges, switches = convert_achraf(
            (SOURCES / "achraf_level4.txt").read_text(encoding="utf-8"))
        self.assertEqual((len(grid), len(grid[0]), start), (6, 17, [3, 1]))
        self.assertEqual(bridges, [
            {"id": "b01", "cells": [[3, 5], [3, 6]], "initial_open": False},
            {"id": "b02", "cells": [[4, 11], [4, 12]], "initial_open": False},
        ])
        self.assertEqual(switches, [
            {"id": "s01", "cell": [1, 9], "type": "heavy",
             "effect": {"mode": "toggle", "targets": ["b02"]}},
            {"id": "s02", "cell": [2, 3], "type": "soft",
             "effect": {"mode": "toggle", "targets": ["b01"]}},
        ])
        padded, *_ = convert_achraf("SFT\nF\n")
        self.assertEqual(padded[1], ["floor", "void", "void"])
        grid, *_ = convert_achraf((SOURCES / "achraf_level7.txt").read_text(encoding="utf-8"))
        self.assertEqual(len(grid), 12)
        self.assertEqual(grid[-1], ["void"] * 17)

    def test_achraf_rejects_bad_source(self):
        for text in ("", "\n\n", "SFT?", "SFFT0", "FFT", "SSFT", "SFF"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                convert_achraf(text)

    def test_frank_real_split_and_permanent(self):
        levels = self.frank_levels()
        original = copy.deepcopy(levels)
        _, start, bridges, switches = convert_frank(levels["levelre"])
        self.assertEqual(start, [4, 1])
        self.assertEqual(bridges, [])
        self.assertEqual(switches, [{"id": "s01", "cell": [4, 13], "type": "split",
                                    "destinations": [[4, 12], [4, 2]], "active_destination": 0}])
        _, _, bridges, switches = convert_frank(levels["leveldw"])
        self.assertEqual(bridges, [{"id": "b01", "cells": [[0, 6], [1, 6]], "initial_open": True}])
        self.assertEqual(switches[0]["effect"], {"mode": "permanent", "targets": ["b01"], "open": False})
        self.assertEqual(levels, original)

    def test_frank_rejects_nonliteral_code(self):
        for text in ("import os", "levelx = []\nlevelx.append(open('x'))",
                     "levelx = []\nlevelx.extend([])", "levelx = []\nlevelx = []"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_frank(text)

    def test_frank_rejects_bad_metadata(self):
        levels = self.frank_levels()
        bad = copy.deepcopy(levels["levelub"])
        bad[11]["swatch123"][1][2] = "off"
        with self.assertRaisesRegex(ValueError, "mixed effects"):
            convert_frank(bad)
        bad = copy.deepcopy(levels["levelss"])
        bad[12]["swatch44"] = [10, 1, 10, 2]
        with self.assertRaisesRegex(ValueError, "nonadjacent"):
            convert_frank(bad)
        bad[12]["swatch44"] = [4, 4, 10, 2]
        with self.assertRaisesRegex(ValueError, "floor"):
            convert_frank(bad)
        bad = copy.deepcopy(levels["levelub"])
        bad[11]["swatch123"][0][:2] = [0, 0]
        with self.assertRaisesRegex(ValueError, "bridge"):
            convert_frank(bad)

    def test_cli_writes_json_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            command = [sys.executable, str(ROOT / "data/references/convert_maps.py"),
                       "fragile_01", "--output-dir", folder]
            first = subprocess.run(command, capture_output=True, text=True, cwd=folder)
            self.assertEqual(first.returncode, 0, first.stderr)
            path = Path(folder) / "fragile_01.json"
            before = path.read_bytes()
            self.assertEqual(json.loads(before), convert("fragile_01"))
            second = subprocess.run(command, capture_output=True, text=True, cwd=folder)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(path.read_bytes(), before)


class MapDataAssertions:
    def coordinate(self, data, cell):
        self.assertIsInstance(cell, list)
        self.assertEqual(len(cell), 2)
        for value, limit in zip(cell, (data["rows"], data["cols"])):
            self.assertIs(type(value), int)
            self.assertLessEqual(0, value)
            self.assertLess(value, limit)
        return data["grid"][cell[0]][cell[1]]

    def check_schema(self, data):
        self.assertEqual(set(data) - {"expected_solvable"}, {"schema_version", "id", "name", "difficulty", "rows", "cols",
                                     "grid", "start", "bridges", "switches", "source"})
        if "expected_solvable" in data:
            self.assertIs(type(data["expected_solvable"]), bool)
        self.assertIs(type(data["schema_version"]), int)
        self.assertEqual(data["schema_version"], 1)
        for key in ("id", "name"):
            self.assertIsInstance(data[key], str)
            self.assertTrue(data[key].strip())
        self.assertIn(data["difficulty"], {"easy", "medium", "hard"})
        for key in ("rows", "cols"):
            self.assertIs(type(data[key]), int)
            self.assertGreater(data[key], 0)
        grid = data["grid"]
        self.assertIsInstance(grid, list)
        self.assertEqual(len(grid), data["rows"])
        cells = {}
        for r, row in enumerate(grid):
            self.assertIsInstance(row, list)
            self.assertEqual(len(row), data["cols"])
            for c, tile in enumerate(row):
                self.assertIn(tile, {"void", "floor", "goal", "fragile", "bridge", "soft", "heavy", "split"})
                cells.setdefault(tile, set()).add((r, c))
        self.assertEqual(len(cells.get("goal", set())), 1)
        self.assertEqual(self.coordinate(data, data["start"]), "floor")
        ids, covered = set(), set()
        self.assertIsInstance(data["bridges"], list)
        for bridge in data["bridges"]:
            self.assertEqual(set(bridge), {"id", "cells", "initial_open"})
            self.assertIsInstance(bridge["id"], str)
            self.assertTrue(bridge["id"].strip())
            self.assertNotIn(bridge["id"], ids)
            ids.add(bridge["id"])
            self.assertIs(type(bridge["initial_open"]), bool)
            self.assertIsInstance(bridge["cells"], list)
            self.assertTrue(bridge["cells"])
            for cell in bridge["cells"]:
                self.assertEqual(self.coordinate(data, cell), "bridge")
                self.assertNotIn(tuple(cell), covered)
                covered.add(tuple(cell))
        self.assertEqual(covered, cells.get("bridge", set()))
        switch_ids, covered = set(), set()
        self.assertIsInstance(data["switches"], list)
        for switch in data["switches"]:
            self.assertIsInstance(switch["id"], str)
            self.assertTrue(switch["id"].strip())
            self.assertNotIn(switch["id"], switch_ids)
            switch_ids.add(switch["id"])
            self.assertIn(switch["type"], {"soft", "heavy", "split"})
            self.assertEqual(self.coordinate(data, switch["cell"]), switch["type"])
            self.assertNotIn(tuple(switch["cell"]), covered)
            covered.add(tuple(switch["cell"]))
            if switch["type"] == "split":
                self.assertEqual(set(switch), {"id", "cell", "type", "destinations", "active_destination"})
                self.assertIsInstance(switch["destinations"], list)
                self.assertEqual(len(switch["destinations"]), 2)
                for cell in switch["destinations"]:
                    self.assertEqual(self.coordinate(data, cell), "floor")
                self.assertGreater(sum(abs(a-b) for a, b in zip(*switch["destinations"])), 1)
                self.assertIs(type(switch["active_destination"]), int)
                self.assertIn(switch["active_destination"], (0, 1))
            else:
                self.assertEqual(set(switch), {"id", "cell", "type", "effect"})
                effect = switch["effect"]
                self.assertIn(effect["mode"], {"toggle", "permanent"})
                self.assertEqual(set(effect), {"mode", "targets"} | ({"open"} if effect["mode"] == "permanent" else set()))
                if effect["mode"] == "permanent":
                    self.assertIs(type(effect["open"]), bool)
                self.assertIsInstance(effect["targets"], list)
                self.assertTrue(effect["targets"])
                self.assertEqual(len(effect["targets"]), len(set(effect["targets"])))
                self.assertLessEqual(set(effect["targets"]), ids)
        self.assertEqual(covered, set().union(*(cells.get(tile, set()) for tile in ("soft", "heavy", "split"))))
        source = data["source"]
        self.assertIn(source["kind"], {"original", "adapted"})
        self.assertEqual(set(source), {"kind", "reference"} |
                         ({"conversion_notes"} if source["kind"] == "adapted" else set()))
        for key in set(source) - {"kind"}:
            self.assertIsInstance(data["source"][key], str)
            self.assertTrue(data["source"][key].strip())


class TestConvertedMapData(MapDataAssertions, unittest.TestCase):
    def files(self):
        return [ROOT / "data/maps" / stage / f"{map_id}.json"
                for stage in ("", "drafts") for map_id in EXPECTED_IDS
                if (ROOT / "data/maps" / stage / f"{map_id}.json").exists()]

    def test_existing_conversions_match_sources_and_schema(self):
        files = self.files()
        self.assertEqual(set(MAPS), EXPECTED_IDS)
        self.assertEqual({p.stem for p in files}, EXPECTED_IDS)
        self.assertEqual(len(files), len({p.stem for p in files}))
        for path in files:
            with self.subTest(map_id=path.stem):
                self.assertIn(path.stem, MAPS)
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["id"], path.stem)
                self.check_schema(data)
                self.assertEqual(data["source"]["kind"], "adapted")
                self.assertNotIn("expected_solvable", data)
                self.assertEqual(data, convert(path.stem))

    def test_achraf_grid_and_switch_links_preserve_source(self):
        tiles = {".": "void", "-": "void", "F": "floor", "S": "floor", "T": "goal", "O": "fragile"}
        for path in self.files():
            source, level, _ = MAPS[path.stem]
            if source != "achraf":
                continue
            with self.subTest(map_id=path.stem):
                data = json.loads(path.read_text(encoding="utf-8"))
                rows = (SOURCES / f"achraf_{level}.txt").read_text(encoding="utf-8").splitlines()
                self.assertEqual(data["rows"], len(rows))
                self.assertEqual(data["cols"], max(map(len, rows)))
                self.assertEqual(rows[data["start"][0]][data["start"][1]], "S")
                bridge_codes = {}
                for bridge in data["bridges"]:
                    codes = {rows[r][c] for r, c in bridge["cells"]}
                    self.assertEqual(len(codes), 1)
                    bridge_codes[bridge["id"]] = codes.pop()
                    self.assertFalse(bridge["initial_open"])
                for r, row in enumerate(data["grid"]):
                    for c, tile in enumerate(row):
                        code = rows[r][c] if c < len(rows[r]) else "."
                        expected = tiles.get(code, "bridge" if code.islower() else "heavy" if code.isdigit() else "soft")
                        self.assertEqual(tile, expected)
                for switch in data["switches"]:
                    r, c = switch["cell"]
                    code = rows[r][c]
                    expected = chr(ord("a") + int(code)) if code.isdigit() else code.lower()
                    self.assertEqual(switch["effect"]["mode"], "toggle")
                    self.assertEqual([bridge_codes[bridge_id] for bridge_id in switch["effect"]["targets"]], [expected])

    def test_catalog_hashes_notes_and_notices_are_present(self):
        catalog = (ROOT / "data/maps/README.md").read_text(encoding="utf-8")
        for path in self.files():
            with self.subTest(map_id=path.stem):
                data = json.loads(path.read_text(encoding="utf-8"))
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                row = next(line for line in catalog.splitlines() if f"[`{path.stem}`](" in line)
                self.assertIn(digest, row)
                self.assertIn("Đạt | Chưa chạy | Chưa chạy", " | ".join(cell.strip() for cell in row.split("|")))
                notes = (ROOT / data["source"]["conversion_notes"]).read_text(encoding="utf-8")
                self.assertIn(f"### `{path.stem}`", notes)
                self.assertIn(MAPS[path.stem][1], notes)
                notice = "AchrafMez-LICENSE.txt" if MAPS[path.stem][0] == "achraf" else "FrankBuss-license.txt"
                self.assertIn(notice, notes)
                self.assertTrue((ROOT / "data/references" / notice).is_file())
        expected_notices = {
            "AchrafMez-LICENSE.txt": "42a2d09d2b6a927b8754ae6f8b72bd77c5ec56c0221896a9ed4b125ced9a1196",
            "FrankBuss-license.txt": "3811ab0b0c1ee1d7c9c6709f6ea180ee712ab2a6a4ceee4930ea579f02c536ce",
        }
        for name, digest in expected_notices.items():
            self.assertEqual(hashlib.sha256((ROOT / "data/references" / name).read_bytes()).hexdigest(), digest)
        for filename in ("achraf-map-conversion.md", "frank-map-conversion.md", "map_sources/README.md"):
            path = ROOT / "data/references" / filename
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if not target.startswith("https://"):
                    self.assertTrue((path.parent / target.split("#")[0]).exists(), target)

    def test_frank_grid_and_all_effects_preserve_source(self):
        levels = read_frank((SOURCES / "frank_selected.txt").read_text(encoding="utf-8"))
        for path in self.files():
            source, level, _ = MAPS[path.stem]
            if source != "frank":
                continue
            with self.subTest(map_id=path.stem):
                data = json.loads(path.read_text(encoding="utf-8"))
                original = levels[level]
                bridges = {bridge["id"]: bridge for bridge in data["bridges"]}
                codes = {"void": " ", "floor": "b", "goal": "e", "fragile": "f", "soft": "s", "heavy": "h", "split": "v"}
                for r, row in enumerate(data["grid"]):
                    for c, tile in enumerate(row):
                        self.assertTrue(original[r][c] in "lrkq" if tile == "bridge" else original[r][c] == codes[tile])
                for bridge in bridges.values():
                    for r, c in bridge["cells"]:
                        self.assertEqual(bridge["initial_open"], original[r][c] in "kq")
                self.assertEqual(data["start"], original[10][::-1])
                for switch in data["switches"]:
                    r, c = switch["cell"]
                    key = f"swatch{c}{r}"
                    if switch["type"] == "split":
                        x1, y1, x2, y2 = original[12][key]
                        self.assertEqual(switch["destinations"], [[y1, x1], [y2, x2]])
                        self.assertEqual(switch["active_destination"], 0)
                    else:
                        effect = switch["effect"]
                        mode = "onoff" if effect["mode"] == "toggle" else "on" if effect["open"] else "off"
                        expanded = sorted([c, r, mode] for bridge_id in effect["targets"] for r, c in bridges[bridge_id]["cells"])
                        self.assertEqual(expanded, sorted(original[11][key]))


if __name__ == "__main__":
    unittest.main()
