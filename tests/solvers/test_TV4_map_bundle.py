import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unittest

from tests.solvers import test_TV4_map_conversion as conversion


ROOT = Path(__file__).resolve().parents[2]
GROUPS = {
    "basic": 4, "fragile": 2, "bridge": 1, "soft_toggle": 2, "heavy": 2,
    "permanent": 2, "split_merge": 2, "combined": 2, "advanced_unsolvable": 1,
}


def geometry_key(data):
    # Reject even rewired copies of the same floor plan, including rotations/reflections.
    cells = [(r, c, "goal" if tile == "goal" else "floor")
             for r, row in enumerate(data["grid"]) for c, tile in enumerate(row)
             if tile != "void"]
    cells.append((*data["start"], "start"))
    variants = []
    for reflected in (False, True):
        for turns in range(4):
            transformed = []
            for r, c, role in cells:
                if reflected:
                    c = -c
                for _ in range(turns):
                    r, c = c, -r
                transformed.append((r, c, role))
            r0 = min(r for r, _, _ in transformed)
            c0 = min(c for _, c, _ in transformed)
            variants.append(tuple(sorted((r-r0, c-c0, role) for r, c, role in transformed)))
    return min(variants)


class TestMapBundle(conversion.MapDataAssertions, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "data/map_bundle.json").read_text(encoding="utf-8"))
        cls.entries = cls.manifest["maps"]

    def test_inventory_is_exact_and_covers_required_groups(self):
        self.assertEqual(self.manifest["version"], 1)
        self.assertEqual(self.manifest["map_count"], 18)
        self.assertEqual(len(self.entries), 18)
        self.assertEqual(len({e["id"] for e in self.entries}), 18)
        paths = [e["path"] for e in self.entries]
        self.assertEqual(len(set(paths)), 18)
        engine_fixtures = {
            "data/maps/advanced_bridge_01.json",
            "data/maps/advanced_split_01.json",
        }
        actual = {
            p.relative_to(ROOT).as_posix() for p in (ROOT / "data/maps").glob("*.json")
        } - engine_fixtures
        self.assertEqual(set(paths), actual)
        self.assertEqual(len(actual), 18)
        self.assertTrue(all(Path(p).parent.as_posix() == "data/maps" for p in paths))
        self.assertEqual(Counter(e["group"] for e in self.entries), GROUPS)
        self.assertFalse(any("drafts" in Path(p).parts for p in paths))

    def test_schema_hashes_sources_and_evidence_match_every_entry(self):
        catalog = (ROOT / "data/maps/README.md").read_text(encoding="utf-8")
        for entry in self.entries:
            with self.subTest(map_id=entry["id"]):
                path = ROOT / entry["path"]
                data = json.loads(path.read_text(encoding="utf-8"))
                self.check_schema(data)
                self.assertEqual(data["id"], entry["id"])
                self.assertEqual(path.stem, entry["id"])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"])
                self.assertEqual(data["source"], entry["source"])
                self.assertEqual(data["difficulty"], entry["difficulty"])
                self.assertIn(entry["sha256"], catalog)
                self.assertEqual(entry["status"], {
                    "data": "passed", "engine": "not_run", "replay": "not_run", "solver": "not_run",
                })
                evidence_path, anchor = entry["evidence"].split("#")
                evidence = (ROOT / evidence_path).read_text(encoding="utf-8")
                self.assertEqual(anchor, entry["id"])
                self.assertIn(f'<a id="{anchor}"></a>', evidence)
                self.assertIn(entry["confidence"], {"manual_reference", "manual_local", "manual_invariant"})
                if data["source"]["kind"] == "adapted":
                    notes = (ROOT / data["source"]["conversion_notes"]).read_text(encoding="utf-8")
                    notice = ROOT / entry["notice"]
                    self.assertTrue(notice.is_file())
                    self.assertIn(notice.name, notes)
                    self.assertIn(entry["id"], notes)
                    if entry["group"] != "basic":
                        self.assertNotIn("expected_solvable", data)
                else:
                    self.assertIsNone(entry["notice"])
        self.assertEqual(Counter(e["source"]["kind"] for e in self.entries), {"original": 4, "adapted": 14})

    def test_maps_have_distinct_geometry_under_all_symmetries(self):
        seen = {}
        for entry in self.entries:
            data = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
            key = geometry_key(data)
            self.assertNotIn(key, seen, f'{entry["id"]} duplicates {seen.get(key)}')
            seen[key] = entry["id"]

    def test_group_assignments_have_the_required_mechanisms(self):
        for entry in self.entries:
            with self.subTest(map_id=entry["id"]):
                data = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
                tiles = {tile for row in data["grid"] for tile in row}
                group = entry["group"]
                effects = [s["effect"] for s in data["switches"] if "effect" in s]
                if group == "basic":
                    self.assertLessEqual(tiles, {"void", "floor", "goal"})
                elif group == "fragile":
                    self.assertIn("fragile", tiles)
                elif group in {"bridge", "soft_toggle", "heavy"}:
                    self.assertTrue(data["bridges"])
                    switch_type = "soft" if group == "soft_toggle" else "heavy"
                    self.assertTrue(any(s["type"] == switch_type and s["effect"]["mode"] == "toggle"
                                        for s in data["switches"]))
                elif group == "permanent":
                    self.assertTrue(any(e["mode"] == "permanent" and e["open"] is
                                        (entry["id"] == "permanent_open_01") for e in effects))
                elif group in {"split_merge", "combined"}:
                    self.assertIn("split", tiles)
                    if group == "combined":
                        self.assertTrue(data["bridges"])
                        self.assertTrue(effects)
                else:
                    self.assertIs(data["expected_solvable"], False)
                    self.assertTrue(data["bridges"])
                    self.assertTrue(effects)

    def test_duplicate_check_ignores_names_padding_rotation_and_reflection(self):
        data = {"grid": [["floor", "floor", "goal"], ["void", "floor", "void"]], "start": [0, 0]}
        key = geometry_key(data)
        for reflected in (False, True):
            grid = copy.deepcopy(data["grid"])
            r, c = data["start"]
            if reflected:
                grid = [row[::-1] for row in grid]
                c = len(grid[0]) - 1 - c
            for _ in range(4):
                grid = [list(row) for row in zip(*grid[::-1])]
                r, c = c, len(grid[0]) - 1 - r
                padded = [["void"] * (len(grid[0]) + 2)]
                padded += [["void", *row, "void"] for row in grid]
                padded += [["void"] * (len(grid[0]) + 2)]
                self.assertEqual(key, geometry_key({"id": "renamed", "grid": padded, "start": [r+1, c+1]}))
        changed = copy.deepcopy(data)
        changed["start"] = [1, 1]
        self.assertNotEqual(key, geometry_key(changed))

    def test_original_fixture_matches_closed_bridge_analysis(self):
        data = json.loads((ROOT / "data/maps/advanced_unsolvable_01.json").read_text(encoding="utf-8"))
        codes = {"void": ".", "floor": "F", "goal": "G", "bridge": "b", "soft": "s"}
        self.assertEqual(["".join(codes[t] for t in row) for row in data["grid"]],
                         ["..........", ".FFFbbFGF.", ".FFs..FFF.", ".FFF..FFF.", ".........."])
        self.assertEqual(data["start"], [1, 1])
        self.assertIs(data["expected_solvable"], False)
        self.assertEqual(data["bridges"], [{"id": "b01", "cells": [[1, 4], [1, 5]], "initial_open": False}])
        self.assertEqual(data["switches"], [{"id": "s01", "cell": [2, 3], "type": "soft",
                                           "effect": {"mode": "permanent", "targets": ["b01"], "open": False}}])

    def test_schema_assertions_reject_broken_data(self):
        data = json.loads((ROOT / "data/maps/combined_01.json").read_text(encoding="utf-8"))
        for label in ("bool_coordinate", "unknown_target", "duplicate_bridge_cell", "bad_split", "extra_field"):
            bad = copy.deepcopy(data)
            if label == "bool_coordinate":
                bad["start"][0] = True
            elif label == "unknown_target":
                bad["switches"][0]["effect"]["targets"] = ["missing"]
            elif label == "duplicate_bridge_cell":
                bad["bridges"][0]["cells"].append(bad["bridges"][0]["cells"][0])
            elif label == "bad_split":
                bad["switches"][2]["active_destination"] = True
            else:
                bad["solution"] = []
            with self.subTest(case=label), self.assertRaises(AssertionError):
                self.check_schema(bad)

    def test_bundle_document_links_resolve(self):
        for name in ("data/maps/README.md", "data/references/map-bundle-evidence.md"):
            path = ROOT / name
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if not target.startswith(("https://", "http://", "#")):
                    self.assertTrue((path.parent / target.split("#")[0]).exists(), target)


if __name__ == "__main__":
    unittest.main()
