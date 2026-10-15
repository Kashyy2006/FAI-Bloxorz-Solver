import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
MAPS = ROOT / "data/maps"
LAYOUTS = {
    "basic_01": ((".......", ".FFFG..", "......."), [1, 1], True),
    "basic_turn_01": ((".FFF", ".FFF", "FFFG", "FFF."), [0, 2], True),
    "basic_cycle_01": (
        (".........", ".FFFFFFF.", ".FFFFFFF.", ".FFFFFFF.",
         ".FFFFFFG.", ".FFFFFFF.", "........."),
        [1, 1], True,
    ),
    "basic_unsolvable_01": ((".........", ".FFFF..G.", "........."), [1, 1], False),
}
TILES = {".": "void", "F": "floor", "G": "goal"}
UPSTREAM = (
    "https://github.com/matuneville/bloxorz-pathfinding/blob/"
    "6af854a88ac3983ffed2ee12a9e26c4cc338aa76/"
    "bloxorz-solver/tests/levels_testing.rs"
)


class TestTV4Maps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maps = {
            map_id: json.loads((MAPS / f"{map_id}.json").read_text(encoding="utf-8"))
            for map_id in LAYOUTS
        }

    def test_basic_bundle_has_four_unique_ids_and_matching_filenames(self):
        self.assertEqual(
            {path.stem for path in MAPS.glob("basic_*.json")}, set(LAYOUTS),
        )
        self.assertEqual({data["id"] for data in self.maps.values()}, set(LAYOUTS))
        for map_id, data in self.maps.items():
            self.assertEqual(data["id"], map_id)

    def test_basic_contract_fields_and_types(self):
        fields = {
            "schema_version", "id", "name", "difficulty", "rows", "cols",
            "grid", "start", "bridges", "switches", "source", "expected_solvable",
        }
        for map_id, data in self.maps.items():
            with self.subTest(map_id=map_id):
                self.assertEqual(set(data), fields)
                self.assertIs(type(data["schema_version"]), int)
                self.assertEqual(data["schema_version"], 1)
                for name in ("id", "name"):
                    self.assertIsInstance(data[name], str)
                    self.assertTrue(data[name].strip())
                self.assertEqual(data["difficulty"], "easy")
                for name in ("rows", "cols"):
                    self.assertIs(type(data[name]), int)
                    self.assertGreater(data[name], 0)
                self.assertEqual(len(data["grid"]), data["rows"])
                for row in data["grid"]:
                    self.assertEqual(len(row), data["cols"])
                    self.assertLessEqual(set(row), set(TILES.values()))
                self.assertEqual(sum(row.count("goal") for row in data["grid"]), 1)
                self.assertEqual(len(data["start"]), 2)
                for coordinate, limit in zip(data["start"], (data["rows"], data["cols"])):
                    self.assertIs(type(coordinate), int)
                    self.assertGreaterEqual(coordinate, 0)
                    self.assertLess(coordinate, limit)
                row, col = data["start"]
                self.assertEqual(data["grid"][row][col], "floor")
                self.assertEqual(data["bridges"], [])
                self.assertEqual(data["switches"], [])
                self.assertIs(type(data["expected_solvable"]), bool)

    def test_layouts_starts_and_expected_labels_match_fixture_design(self):
        for map_id, (rows, start, solvable) in LAYOUTS.items():
            with self.subTest(map_id=map_id):
                data = self.maps[map_id]
                self.assertEqual(data["grid"], [[TILES[cell] for cell in row] for row in rows])
                self.assertEqual(data["start"], start)
                self.assertIs(data["expected_solvable"], solvable)

    def test_two_rolls_map_matches_full_contract_example(self):
        contract = (ROOT / "docs/contracts/map-format.md").read_text(encoding="utf-8")
        examples = [json.loads(block) for block in re.findall(r"```json\n(.*?)\n```", contract, re.S)
                    if '"id": "basic_01"' in block]
        self.assertEqual(len(examples), 1)
        self.assertEqual(self.maps["basic_01"], examples[0])

    def test_sources_and_adaptation_notes_are_present(self):
        references = (ROOT / "data/references/README.md").read_text(encoding="utf-8")
        for map_id, data in self.maps.items():
            with self.subTest(map_id=map_id):
                source = data["source"]
                self.assertIn(map_id, references)
                self.assertIsInstance(source["reference"], str)
                self.assertTrue(source["reference"].strip())
                if map_id == "basic_turn_01":
                    self.assertEqual(set(source), {"kind", "reference", "conversion_notes"})
                    self.assertEqual(source["kind"], "adapted")
                    self.assertEqual(source["reference"], UPSTREAM)
                    self.assertEqual(source["conversion_notes"], "data/references/basic_turn_01.md")
                    notes = (ROOT / source["conversion_notes"]).read_text(encoding="utf-8")
                    self.assertIn(UPSTREAM, notes)
                    self.assertIn("level_2_2", notes)
                    self.assertIn("matuneville-LICENSE.txt", notes)
                else:
                    self.assertEqual(set(source), {"kind", "reference"})
                    self.assertEqual(source["kind"], "original")

    def test_adapted_layout_preserves_source_matrix(self):
        notes = (ROOT / "data/references/basic_turn_01.md").read_text(encoding="utf-8")
        matrix = json.loads(re.search(r"```json\n(.*?)\n```", notes, re.S).group(1))
        data = self.maps["basic_turn_01"]
        tiles = {0: "void", 1: "floor", 2: "floor", 3: "goal"}
        self.assertEqual(data["grid"], [[tiles[cell] for cell in row] for row in matrix])
        self.assertEqual(
            [[r, c] for r, row in enumerate(matrix) for c, cell in enumerate(row) if cell == 2],
            [data["start"]],
        )
        notice = (ROOT / "data/references/matuneville-LICENSE.txt").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2023 Matías", notice)
        self.assertIn("Permission is hereby granted", notice)

    def test_map_hashes_are_recorded_in_catalog(self):
        catalog = (MAPS / "README.md").read_text(encoding="utf-8")
        for map_id in LAYOUTS:
            with self.subTest(map_id=map_id):
                digest = hashlib.sha256((MAPS / f"{map_id}.json").read_bytes()).hexdigest()
                self.assertIn(f"| `{map_id}` | `{digest}` |", catalog)


if __name__ == "__main__":
    unittest.main()
