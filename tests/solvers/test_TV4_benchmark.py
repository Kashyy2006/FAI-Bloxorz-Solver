"""Benchmark fixtures are never published as game performance data."""

import copy
import csv
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import sys
from types import SimpleNamespace
import tracemalloc

from benchmarks.run import ROOT, _hash, _load_cases, _run_one, _summary, _validate_result, run_benchmark
from src.engine.models import State
from src.solvers.bfs.solver import solve_bfs
from src.solvers.dfs.solver import solve_dfs
from src.solvers.common.result import SolverMetrics, SolverResult


def solved_binding(map_path, snapshot, *, timeout_s):
    return SolverResult(
        map_id=json.loads(map_path.read_text(encoding="utf-8"))["id"],
        algorithm="BFS", status="SOLVED", start_state=snapshot,
        actions=["SWITCH", "RIGHT"], metrics=SolverMetrics(0.25, 1024, 3, 2, 4),
        timeout_s=timeout_s,
    )


def crash_binding(*args, **kwargs):
    os._exit(7)


def blocked_binding(*args, **kwargs):
    import time
    time.sleep(30)


def exception_binding(*args, **kwargs):
    raise RuntimeError("fixture binding failed")


def wrong_snapshot_binding(map_path, snapshot, *, timeout_s):
    result = solved_binding(map_path, snapshot, timeout_s=timeout_s)
    result.start_state = {**snapshot, "active": 1 - snapshot["active"]}
    return result


def null_error_binding(map_path, snapshot, *, timeout_s):
    return SolverResult(None, "BFS", "ERROR", None, None, SolverMetrics(), None,
                        error="snapshot rejected by fixture validator")


def nonfinite_binding(map_path, snapshot, *, timeout_s):
    result = solved_binding(map_path, snapshot, timeout_s=timeout_s)
    result.metrics.search_time_s = float("nan")
    return result


def _graph_binding(map_path, snapshot, timeout_s, solver):
    # Coordinates label fixture nodes; they are not Bloxorz transitions.
    if tracemalloc.is_tracing():
        raise RuntimeError("runner must not start tracing around the binding")
    ids = tuple(snapshot["bridges"])
    start = State(snapshot["mode"], snapshot["cells"], snapshot["active"],
                  tuple(snapshot["bridges"].values()))
    switched = State("SPLIT", start.cells, 1 - start.active, start.bridges)
    goal = State("UPRIGHT", ((8, 8),), None, start.bridges)
    graph = {start: [SimpleNamespace(action="SWITCH", state=switched, cost=1)],
             switched: [SimpleNamespace(action="RIGHT", state=goal, cost=3)], goal: []}

    def validate(game_map, state):
        if state not in game_map:
            raise ValueError("state is outside the fixture graph")

    return solver(
        graph, start, map_id=json.loads(map_path.read_text(encoding="utf-8"))["id"],
        bridge_ids=ids, state_key=lambda state: (state.mode, state.cells, state.active, state.bridges),
        is_goal=lambda game_map, state: state == goal,
        successors=lambda game_map, state: game_map[state], validate_start_state=validate,
        timeout_s=timeout_s,
    )


def bfs_graph_binding(map_path, snapshot, *, timeout_s):
    return _graph_binding(map_path, snapshot, timeout_s, solve_bfs)


def dfs_graph_binding(map_path, snapshot, *, timeout_s):
    return _graph_binding(map_path, snapshot, timeout_s, solve_dfs)


class TestBenchmarkProcess(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "map.json"
        self.path.write_text('{"id":"fixture"}', encoding="utf-8")
        self.case = {
            "map_id": "fixture", "map_path": str(self.path),
            "map_sha256": _hash(self.path.read_bytes()),
            "start_state": {"mode": "SPLIT", "cells": [[1, 1], [3, 3]],
                            "active": 1, "bridges": {"b01": True, "b02": False}},
        }

    def test_fresh_process_and_full_result_snapshot(self):
        outputs = [_run_one(solved_binding, self.case, 60, 5) for _ in range(2)]
        self.assertEqual(len({o["worker_pid"] for o in outputs}), 2)
        for output in outputs:
            self.assertNotEqual(output["worker_pid"], os.getpid())
            self.assertEqual(output["exitcode"], 0)
            result = _validate_result(output["result"], self.case, "BFS", 60)
            self.assertEqual(result["start_state"], self.case["start_state"])
            self.assertEqual(result["metrics"]["search_time_s"], 0.25)

    def test_crashed_process_has_no_fabricated_solver_status(self):
        output = _run_one(crash_binding, self.case, 60, 5)
        self.assertEqual(output["exitcode"], 7)
        self.assertEqual(output["issue"], "process_error")
        self.assertNotIn("result", output)

    def test_noncooperative_process_is_stopped_without_solver_timeout(self):
        output = _run_one(blocked_binding, self.case, 0.1, 0.5)
        self.assertEqual(output["issue"], "process_error")
        self.assertGreaterEqual(output["wall_time_s"], 0.6)
        self.assertNotIn("result", output)

    def test_unpicklable_callable_is_a_process_error(self):
        output = _run_one(lambda *args: None, self.case, 60, 5)
        self.assertEqual(output["issue"], "process_error")
        self.assertIsNone(output["worker_pid"])

    def test_binding_import_and_exception_are_separate_readiness_issues(self):
        for binding, issue in (("missing_benchmark_module:solve", "binding_error"),
                               (exception_binding, "solve_error"),
                               (nonfinite_binding, "result_error")):
            with self.subTest(binding=binding):
                output = _run_one(binding, self.case, 60, 5)
                self.assertEqual(output["issue"], issue)
                self.assertNotIn("result", output)

    def test_changed_map_is_rejected_before_binding(self):
        self.path.write_text('{"id":"changed"}', encoding="utf-8")
        output = _run_one(solved_binding, self.case, 60, 5)
        self.assertEqual(output["issue"], "input_error")

    def test_all_statuses_and_error_null_envelope(self):
        raw = solved_binding(self.path, self.case["start_state"], timeout_s=60).to_dict()
        for status in ("SOLVED", "UNSOLVABLE", "TIMEOUT", "CANCELLED", "ERROR"):
            with self.subTest(status=status):
                result = copy.deepcopy(raw)
                result["status"] = status
                if status != "SOLVED":
                    result["actions"] = None
                    result["metrics"].update(solution_length=None, solution_cost=None)
                if status == "ERROR":
                    result.update(error="invalid input", map_id=None, start_state=None, timeout_s=None)
                self.assertEqual(_validate_result(result, self.case, "BFS", 60), result)

    def test_invalid_results_are_rejected(self):
        raw = solved_binding(self.path, self.case["start_state"], timeout_s=60).to_dict()
        mutations = [
            lambda r: r.update(algorithm="DFS"), lambda r: r.update(map_id="other"),
            lambda r: r.update(timeout_s=1), lambda r: r.update(cost_model="wrong"),
            lambda r: r["start_state"].update(active=0),
            lambda r: r["start_state"]["bridges"].update(b01=1),
            lambda r: r["metrics"].update(search_time_s=float("nan")),
            lambda r: r["metrics"].update(expanded_nodes=True),
            lambda r: r["metrics"].update(solution_cost=None),
            lambda r: r.update(status="TIMEOUT"), lambda r: r.update(actions=["FLY", "RIGHT"]),
            lambda r: r.update(extra=1), lambda r: r["metrics"].update(extra=1),
        ]
        for mutate in mutations:
            result = copy.deepcopy(raw)
            mutate(result)
            with self.subTest(result=result), self.assertRaises(ValueError):
                _validate_result(result, self.case, "BFS", 60)


class TestBenchmarkInventoryAndOutput(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / "map.json"
        self.map_data = {"id": "fixture", "start": [1, 1], "bridges": [
            {"id": "b02", "initial_open": False}, {"id": "b01", "initial_open": True}]}
        self.path.write_text(json.dumps(self.map_data), encoding="utf-8")
        self.snapshot = {"mode": "SPLIT", "cells": [[1, 1], [3, 3]],
                         "active": 1, "bridges": {"b01": False, "b02": True}}
        self.entry = {"id": "fixture", "path": "map.json", "sha256": _hash(self.path.read_bytes()),
                      "start_state": self.snapshot}
        self.inventory = self.root / "inventory.json"
        self.write_inventory()
        self.output = self.root / "results"

    def write_inventory(self):
        self.inventory.write_text(json.dumps({"maps": [self.entry]}), encoding="utf-8")

    def run_benchmark(self, bindings, **kwargs):
        return run_benchmark(self.inventory, bindings, self.output, root=self.root, **kwargs)

    def test_inventory_snapshot_hash_initial_state_and_full_bundle(self):
        cases, digest = _load_cases(self.inventory, self.root)
        self.assertEqual(cases[0]["start_state"], self.snapshot)
        self.assertEqual(digest, _hash(self.inventory.read_bytes()))
        del self.entry["start_state"]
        self.write_inventory()
        initial, _ = _load_cases(self.inventory, self.root)
        self.assertEqual(initial[0]["start_state"], {
            "mode": "UPRIGHT", "cells": [[1, 1]], "active": None,
            "bridges": {"b01": True, "b02": False}})
        self.assertNotEqual(cases[0]["snapshot_sha256"], initial[0]["snapshot_sha256"])
        bundle, _ = _load_cases(ROOT / "data/map_bundle.json", ROOT)
        self.assertEqual(len(bundle), 18)
        self.assertEqual(sum("prepared" in c["map_path"] for c in bundle), 14)

    def test_bad_inventory_fails_before_creating_output(self):
        for change in ({"sha256": "0" * 64}, {"id": "wrong"}, {"start_state": None},
                       {"start_state": {**self.snapshot, "bridges": {}}}):
            with self.subTest(change=change):
                original = copy.deepcopy(self.entry)
                self.entry.update(change)
                self.write_inventory()
                with self.assertRaises((ValueError, TypeError)):
                    self.run_benchmark({})
                self.assertFalse(self.output.exists())
                self.entry = original

    def test_three_runs_json_csv_metadata_summary_and_missing_bindings(self):
        report = self.run_benchmark({"BFS": solved_binding})
        self.assertTrue(report["complete"])
        self.assertEqual(len(report["runs"]), 3)
        self.assertEqual([r["run_index"] for r in report["runs"]], [1, 2, 3])
        self.assertEqual(len({r["worker_pid"] for r in report["runs"]}), 3)
        self.assertEqual(len(report["readiness"]), 3)
        self.assertTrue(all(r["run_index"] is None for r in report["readiness"]))
        self.assertTrue(all(r["issue"] == "missing_binding" for r in report["readiness"]))
        self.assertEqual(json.loads((self.output / "report.json").read_text(encoding="utf-8")), report)
        with (self.output / "runs.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 3)
        for row, run in zip(rows, report["runs"]):
            self.assertEqual(json.loads(row["result_json"]), run["result"])
            self.assertEqual(row["snapshot_sha256"], run["snapshot_sha256"])
            self.assertEqual(float(row["search_time_s"]), 0.25)
        with (self.output / "readiness.csv").open(encoding="utf-8", newline="") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))), 3)
        self.assertEqual(report["summary"][0]["median_search_time_s"], 0.25)
        self.assertEqual(report["summary"][0]["SOLVED"], 3)
        self.assertIsNone(report["summary"][1]["median_search_time_s"])
        environment = report["environment"]
        for key in ("machine", "platform", "processor", "python", "code_commit", "source_sha256",
                    "inventory_sha256", "timeout_s", "runs_per_pair"):
            self.assertIn(key, environment)
        self.assertEqual(environment["timeout_s"], 60)
        self.assertEqual(environment["runs_per_pair"], 3)
        original = (self.output / "report.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_benchmark({})
        self.assertEqual((self.output / "report.json").read_bytes(), original)

    def test_real_public_solvers_run_in_spawned_processes_on_fixture_graph(self):
        report = self.run_benchmark({"BFS": bfs_graph_binding, "DFS": dfs_graph_binding},
                                    algorithms=("BFS", "DFS"))
        self.assertFalse(report["readiness"])
        self.assertEqual(len(report["runs"]), 6)
        for record in report["runs"]:
            result = record["result"]
            self.assertEqual(result["actions"], ["SWITCH", "RIGHT"])
            self.assertEqual(result["metrics"]["solution_cost"], 4)
            self.assertGreater(result["metrics"]["peak_memory_bytes"], 0)
            self.assertEqual(result["start_state"], self.snapshot)

    def test_invalid_result_and_binding_failure_never_enter_performance_rows(self):
        report = self.run_benchmark({"BFS": wrong_snapshot_binding,
                                     "DFS": "missing_benchmark_module:solve"},
                                    algorithms=("BFS", "DFS"))
        self.assertFalse(report["runs"])
        self.assertEqual(len(report["readiness"]), 6)
        self.assertEqual({r["issue"] for r in report["readiness"]}, {"invalid_result", "binding_error"})
        self.assertTrue(all(r["run_index"] in (1, 2, 3) for r in report["readiness"]))

    def test_error_null_fields_survive_json_csv_without_substitution(self):
        report = self.run_benchmark({"BFS": null_error_binding}, algorithms=("BFS",))
        self.assertFalse(report["readiness"])
        self.assertEqual(report["summary"][0]["ERROR"], 3)
        self.assertIsNone(report["summary"][0]["median_search_time_s"])
        for record in report["runs"]:
            self.assertIsNone(record["result"]["map_id"])
            self.assertIsNone(record["result"]["start_state"])
            self.assertIsNone(record["result"]["timeout_s"])

    def test_summary_excludes_unsolved_measurements(self):
        cases, _ = _load_cases(self.inventory, self.root)
        runs = []
        for status, value in (("SOLVED", 1), ("TIMEOUT", 60), ("SOLVED", 3)):
            runs.append({"map_id": "fixture", "algorithm": "BFS", "result": {
                "status": status, "metrics": {name: value for name in (
                    "search_time_s", "peak_memory_bytes", "expanded_nodes", "solution_length", "solution_cost")}}})
        summary = _summary(cases, ("BFS",), runs, [])[0]
        self.assertEqual(summary["median_search_time_s"], 2)
        self.assertEqual(summary["SOLVED"], 2)
        self.assertEqual(summary["TIMEOUT"], 1)

    def test_cli_direct_and_module_entries_are_safe_on_windows(self):
        for index, entrypoint in enumerate(([str(ROOT / "benchmarks/run.py")], ["-m", "benchmarks.run"])):
            with self.subTest(entrypoint=entrypoint):
                output = self.root / f"cli{index}"
                command = [sys.executable, *entrypoint, "--inventory", str(self.inventory),
                           "--root", str(self.root), "--output", str(output), "--algorithms", "BFS",
                           "--binding", "BFS=tests.solvers.test_TV4_benchmark:bfs_graph_binding"]
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                report = json.loads((output / "report.json").read_text(encoding="utf-8"))
                self.assertEqual(len(report["runs"]), 3)
                self.assertFalse(report["readiness"])

    def test_missing_bindings_do_not_start_processes(self):
        with patch("benchmarks.run._run_one") as worker:
            report = self.run_benchmark({})
        worker.assert_not_called()
        self.assertFalse(report["runs"])
        self.assertEqual(len(report["readiness"]), 4)

    def test_incompatible_binding_is_recorded_as_readiness(self):
        report = self.run_benchmark({"BFS": None}, algorithms=("BFS",))
        self.assertFalse(report["runs"])
        self.assertEqual(len(report["readiness"]), 3)
        self.assertTrue(all(r["issue"] == "binding_error" for r in report["readiness"]))

    def test_completed_runs_are_saved_before_interruption(self):
        cases, _ = _load_cases(self.inventory, self.root)
        result = solved_binding(self.path, cases[0]["start_state"], timeout_s=60).to_dict()
        message = {"result": result, "worker_pid": 123, "exitcode": 0, "wall_time_s": 1}
        with patch("benchmarks.run._run_one", side_effect=[message, KeyboardInterrupt]):
            with self.assertRaises(KeyboardInterrupt):
                self.run_benchmark({"BFS": solved_binding})
        report = json.loads((self.output / "report.json").read_text(encoding="utf-8"))
        self.assertFalse(report["complete"])
        self.assertEqual(len(report["runs"]), 1)


if __name__ == "__main__":
    unittest.main()
