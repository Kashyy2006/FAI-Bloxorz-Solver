"""Real GUI/solver boundary tests for advanced maps and shared costs."""
import copy
import json
import threading
import unittest
from pathlib import Path

from src.engine import (Status, initial_state, is_goal, load_map, state_to_dict,
                        state_from_dict, step_cost, transition)
from src.solvers.solve import solve
from src.gui.solver.result import validate_result

ROOT = Path(__file__).resolve().parents[2]


class SharedAdvancedEngineTest(unittest.TestCase):
    def test_all_algorithms_replay_each_map_with_identical_engine_costs(self):
        for filename in ("advanced_bridge_01.json", "advanced_split_01.json",
                         "basic_01.json", "basic_turn_01.json", "basic_cycle_01.json"):
            m = load_map(ROOT / "data/maps" / filename)
            raw = json.loads((ROOT / "data/maps" / filename).read_text(encoding="utf-8"))
            start = initial_state(m)
            for algorithm in ("BFS", "DFS", "UCS", "ASTAR"):
                with self.subTest(map=filename, algorithm=algorithm):
                    snapshot = state_to_dict(m, start)
                    result = solve(raw, snapshot, algorithm, timeout_s=5)
                    self.assertEqual(result["status"], "SOLVED", result)
                    validate_result(result, raw, snapshot, algorithm, 5)
                    current, total = start, 0
                    for action in result["actions"]:
                        moved = transition(m, current, action)
                        self.assertIn(moved.status, (Status.OK, Status.WON))
                        total += step_cost(m, current, action, moved.next_state)
                        current = moved.next_state
                    self.assertTrue(is_goal(m, current))
                    self.assertEqual(result["metrics"]["solution_cost"], total)
                    if algorithm in ("BFS", "UCS", "ASTAR") and filename == "advanced_bridge_01.json":
                        self.assertEqual(total, 10)

    def test_solving_current_split_snapshot_preserves_active_and_flags(self):
        m = load_map(ROOT / "data/maps/advanced_split_01.json")
        current = initial_state(m)
        for action in ("RIGHT", "RIGHT", "SWITCH"):
            current = transition(m, current, action).next_state
        for algorithm in ("BFS", "DFS", "UCS", "ASTAR"):
            with self.subTest(algorithm=algorithm):
                result = solve(m, current, algorithm, timeout_s=5)
                self.assertEqual(result["status"], "SOLVED", result)
                self.assertEqual(state_from_dict(m, result["start_state"]), current)
                end = current
                for action in result["actions"]:
                    end = transition(m, end, action).next_state
                self.assertTrue(is_goal(m, end))

    def test_cancel_timeout_and_unsolvable_use_standard_results(self):
        m = load_map(ROOT / "data/maps/advanced_bridge_01.json")
        start = initial_state(m)
        cancel = threading.Event(); cancel.set()
        no_path = load_map(ROOT / "data/maps/basic_unsolvable_01.json")
        for algorithm in ("BFS", "DFS", "UCS", "ASTAR"):
            with self.subTest(algorithm=algorithm):
                self.assertEqual(solve(m, start, algorithm, cancel_event=cancel)["status"], "CANCELLED")
                self.assertEqual(solve(m, start, algorithm, timeout_s=1e-12)["status"], "TIMEOUT")
                result = solve(no_path, initial_state(no_path), algorithm)
                self.assertEqual(result["status"], "UNSOLVABLE")
                self.assertIsNone(result["actions"])
                self.assertIsNone(result["metrics"]["solution_cost"])

    def test_gui_and_engine_match_for_advanced_moves_and_bridge_visibility(self):
        from src.gui.manual.game import _initial_state, _move, _visible_grid
        raw = json.loads((ROOT / "data/maps/advanced_bridge_01.json").read_text())
        saved = copy.deepcopy(raw)
        m = load_map(ROOT / "data/maps/advanced_bridge_01.json")
        gui = _initial_state(raw)
        engine = initial_state(m)
        self.assertEqual(_visible_grid(raw, gui)[1][4], "void")
        for action in ["RIGHT"] * 6:
            engine = transition(m, engine, action).next_state
            gui = _move(gui, action, raw)
            self.assertEqual(state_from_dict(m, gui), engine)
        self.assertEqual(_visible_grid(raw, gui)[1][4], "bridge")
        self.assertEqual(raw, saved)

    def test_gui_reports_fragile_loss_from_engine(self):
        from src.gui.manual.game import _move
        raw = json.loads((ROOT / "data/maps/advanced_bridge_01.json").read_text())
        # A horizontal block on [1,3],[1,4] stands on fragile [1,5].
        gui = {"mode": "HORIZONTAL", "cells": [(1,3),(1,4)], "active": None,
               "bridges": {"b01": True, "b02": False}}
        self.assertIsNone(_move(gui, "RIGHT", raw))

    def test_dispatcher_validation_goal_fast_path_and_benchmark_bindings(self):
        from src.solvers.solve import run_astar, run_bfs, run_dfs, run_ucs
        map_path = ROOT / "data/maps/basic_01.json"
        raw = json.loads(map_path.read_text(encoding="utf-8"))
        m = load_map(map_path)
        snapshot = state_to_dict(m, initial_state(m))
        for algo, binding in (("BFS", run_bfs), ("DFS", run_dfs),
                              ("UCS", run_ucs), ("ASTAR", run_astar)):
            with self.subTest(algorithm=algo):
                res = binding(map_path, snapshot, timeout_s=5.0)
                self.assertEqual(res["status"], "SOLVED")
                validate_result(res, raw, snapshot, algo, 5.0)
                # Pre-solved goal state wins over cancel_event with zero metrics.
                cancel = threading.Event()
                cancel.set()
                goal_state = {"mode": "UPRIGHT", "cells": [list(m.goal)],
                              "active": None, "bridges": {}}
                goal_res = solve(raw, goal_state, algo, timeout_s=5.0, cancel_event=cancel)
                self.assertEqual(goal_res["status"], "SOLVED")
                self.assertEqual(goal_res["actions"], [])
                self.assertEqual(goal_res["metrics"]["expanded_nodes"], 0)
                self.assertEqual(goal_res["metrics"]["solution_cost"], 0)
                # Invalid timeout or bad start state produces valid ERROR result.
                bad_timeout = solve(raw, snapshot, algo, timeout_s=-1)
                self.assertEqual(bad_timeout["status"], "ERROR")
                validate_result(bad_timeout, raw, snapshot, algo, 5.0)


if __name__ == "__main__":
    unittest.main()

