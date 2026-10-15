"""Integration tests for the solver GUI backend (no Pygame needed).

Run from the project root:
    python3 -m unittest tests.integration.test_solver_gui_backend -v
"""

import json
import threading
import time
import unittest
from pathlib import Path

from src.gui.solver import placeholder_solver
from src.gui.solver.replay import Replay
from src.gui.solver.worker import SolverWorker

ROOT = Path(__file__).resolve().parents[2]


def basic_move(state, action, grid):
    """Minimal copy of the manual GUI rolling rules (floor/void only)."""
    mode, cells = state["mode"], state["cells"]
    r, c = cells[0]
    dr, dc = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}[action]
    if mode == "UPRIGHT":
        nxt = ("VERTICAL" if dr else "HORIZONTAL",
               sorted([(r + dr, c + dc), (r + 2 * dr, c + 2 * dc)]))
    elif (mode == "HORIZONTAL" and dc) or (mode == "VERTICAL" and dr):
        nxt = ("UPRIGHT", [(r + dr, c + dc)] if dr + dc < 0 else [(r + 2 * dr, c + 2 * dc)])
    else:
        nxt = (mode, [(x + dr, y + dc) for x, y in cells])
    rows, cols = len(grid), len(grid[0])
    if any(not (0 <= x < rows and 0 <= y < cols) or grid[x][y] == "void" for x, y in nxt[1]):
        return None
    return {"mode": nxt[0], "cells": nxt[1], "active": None}


def load(name):
    return json.loads((ROOT / "data" / "maps" / name).read_text(encoding="utf-8"))


def start_of(game_map):
    return {"mode": "UPRIGHT", "cells": [tuple(game_map["start"])], "active": None}


def wait_result(worker, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        result = worker.poll()
        if result is not None:
            return result
        time.sleep(0.01)
    raise AssertionError("worker produced no result")


class PlaceholderSolverTest(unittest.TestCase):
    def test_basic_01_all_algorithms(self):
        game_map = load("basic_01.json")
        for algo in placeholder_solver.ALGORITHMS:
            result = placeholder_solver.solve(game_map, start_of(game_map), algo,
                                              move_fn=basic_move)
            self.assertEqual(result["status"], "SOLVED", algo)
            self.assertEqual(result["actions"], ["RIGHT", "RIGHT"], algo)
            self.assertEqual(result["metrics"]["solution_cost"], 2)

    def test_unsolvable_and_unknown_algorithm(self):
        game_map = load("basic_01.json")
        game_map["grid"][1][4] = "void"
        game_map["grid"][1][0] = "goal"  # goal unreachable (needs 1 cell to the left)
        result = placeholder_solver.solve(game_map, start_of(game_map), "BFS",
                                          move_fn=basic_move)
        self.assertEqual(result["status"], "UNSOLVABLE")
        self.assertIsNone(result["actions"])
        bad = placeholder_solver.solve(game_map, start_of(game_map), "XYZ", move_fn=basic_move)
        self.assertEqual(bad["status"], "ERROR")

    def test_cancel_before_search(self):
        game_map = load("basic_01.json")
        event = threading.Event()
        event.set()
        result = placeholder_solver.solve(game_map, start_of(game_map), "BFS",
                                          cancel_event=event, move_fn=basic_move)
        self.assertEqual(result["status"], "CANCELLED")


class WorkerTest(unittest.TestCase):
    def test_result_and_stale_runs(self):
        def slow_solve(game_map, state, algorithm, timeout_s, cancel_event):
            while not cancel_event.is_set():
                time.sleep(0.01)
            return {"status": "CANCELLED", "algorithm": algorithm}

        worker = SolverWorker(slow_solve)
        worker.start({}, {}, "BFS")
        worker.cancel()
        self.assertEqual(wait_result(worker)["status"], "CANCELLED")

        worker.start({}, {}, "DFS")
        worker.discard()  # e.g. level changed: result must be ignored
        time.sleep(0.1)
        self.assertIsNone(worker.poll())


class ReplayTest(unittest.TestCase):
    def test_play_step_and_wait_for_ready(self):
        replay = Replay()
        replay.load(["RIGHT", "UP"])
        self.assertEqual(replay.step(), "RIGHT")
        replay.play()
        self.assertIsNone(replay.update(1.0, ready=False))
        self.assertEqual(replay.update(0.0, ready=True), "UP")
        self.assertTrue(replay.done)
        self.assertFalse(replay.playing)


if __name__ == "__main__":
    unittest.main()
