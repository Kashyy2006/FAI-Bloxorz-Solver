"""Deterministic worker lifecycle tests using events, not scheduling assumptions."""

import threading
import unittest

from src.gui.solver.result import validate_result
from src.gui.solver.worker import SolverWorker
from .test_solver_gui_backend import load, start_of, wait_result
from .test_solver_result import solved_result


class WorkerLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.game_map = load("basic_01.json")
        self.state = start_of(self.game_map)
        self.workers = []
        self.releases = []

    def tearDown(self):
        for release in self.releases:
            release.set()
        for worker in self.workers:
            worker.discard()
            if worker._thread:
                worker._thread.join(3)
                self.assertFalse(worker._thread.is_alive())

    def worker(self, solve):
        worker = SolverWorker(solve)
        self.workers.append(worker)
        return worker

    def gate(self):
        event = threading.Event()
        self.releases.append(event)
        return event

    def test_only_latest_replacement_runs_after_old_thread_exits(self):
        entered, release = threading.Event(), self.gate()
        calls = []

        def solve(game_map, state, algorithm, timeout_s, cancel_event):
            calls.append(algorithm)
            if algorithm == "BFS":
                entered.set()
                self.assertTrue(release.wait(3))
            return solved_result(game_map, state, algorithm)

        worker = self.worker(solve)
        worker.start(self.game_map, self.state, "BFS")
        self.assertTrue(entered.wait(2))
        old_thread = worker._thread
        worker.start(self.game_map, self.state, "DFS")
        worker.start(self.game_map, self.state, "ASTAR")
        self.assertIsNone(worker.poll())
        self.assertIs(worker._thread, old_thread)
        self.assertEqual(calls, ["BFS"])
        release.set()
        old_thread.join(3)
        result = wait_result(worker)
        self.assertEqual(result["algorithm"], "ASTAR")
        self.assertEqual(calls, ["BFS", "ASTAR"])

    def test_cancel_beats_already_queued_success_and_is_idempotent(self):
        def solve(game_map, state, algorithm, **kwargs):
            result = solved_result(game_map, state, algorithm)
            result["metrics"].update(search_time_s=0.25, peak_memory_bytes=4096,
                                     expanded_nodes=2)
            return result

        worker = self.worker(solve)
        worker.start(self.game_map, self.state, "BFS")
        worker._thread.join(3)  # SOLVED is queued, but the GUI has not polled it.
        worker.cancel()
        worker.cancel()
        result = wait_result(worker)
        self.assertEqual(result["status"], "CANCELLED")
        self.assertEqual(result["metrics"]["search_time_s"], 0.25)
        self.assertEqual(result["metrics"]["peak_memory_bytes"], 4096)
        self.assertEqual(result["metrics"]["expanded_nodes"], 2)
        validate_result(result, self.game_map, self.state, "BFS", 60.0)
        self.assertIsNone(worker.poll())

    def test_active_cancel_waits_without_blocking_and_drops_late_success(self):
        entered, release = threading.Event(), self.gate()

        def solve(game_map, state, algorithm, **kwargs):
            entered.set()
            release.wait(3)
            return solved_result(game_map, state, algorithm)

        worker = self.worker(solve)
        worker.start(self.game_map, self.state, "BFS")
        self.assertTrue(entered.wait(2))
        worker.cancel()
        self.assertIsNone(worker.poll())
        self.assertTrue(worker._thread.is_alive())
        release.set()
        self.assertEqual(wait_result(worker)["status"], "CANCELLED")

    def test_cancel_pending_job_does_not_start_it(self):
        entered, release = threading.Event(), self.gate()
        calls = []

        def solve(game_map, state, algorithm, **kwargs):
            calls.append(algorithm)
            entered.set()
            release.wait(3)
            return solved_result(game_map, state, algorithm)

        worker = self.worker(solve)
        worker.start(self.game_map, self.state, "BFS")
        self.assertTrue(entered.wait(2))
        worker.start(self.game_map, self.state, "DFS")
        worker.cancel()
        self.assertEqual(wait_result(worker)["algorithm"], "DFS")
        release.set()
        worker._thread.join(3)
        self.assertIsNone(worker.poll())
        self.assertEqual(calls, ["BFS"])

    def test_map_and_state_are_snapshotted_before_pending_launch(self):
        entered, release = threading.Event(), self.gate()

        def solve(game_map, state, algorithm, **kwargs):
            if algorithm == "BFS":
                entered.set()
                release.wait(3)
            return solved_result(game_map, state, algorithm)

        worker = self.worker(solve)
        worker.start(self.game_map, self.state, "BFS")
        self.assertTrue(entered.wait(2))
        worker.start(self.game_map, self.state, "DFS")
        self.game_map["id"] = "mutated"
        self.state["cells"][0] = (9, 9)
        release.set()
        worker._thread.join(3)
        result = wait_result(worker)
        self.assertEqual(result["map_id"], "basic_01")
        self.assertEqual(result["start_state"]["cells"], [[1, 1]])

    def test_exception_and_none_become_full_error_results(self):
        def raises(game_map, state, algorithm, **kwargs):
            game_map["id"] = "mutated"
            state["cells"].clear()
            raise RuntimeError("solver failed")

        for solve in (raises, lambda *args, **kwargs: None):
            with self.subTest(solve=solve):
                worker = self.worker(solve)
                worker.start(self.game_map, self.state, "BFS")
                result = wait_result(worker)
                self.assertEqual(result["status"], "ERROR")
                validate_result(result, self.game_map, self.state, "BFS", 60.0)

    def test_discard_drops_queued_result(self):
        worker = self.worker(lambda m, s, a, **kw: solved_result(m, s, a))
        worker.start(self.game_map, self.state, "BFS")
        worker._thread.join(3)
        worker.discard()
        self.assertIsNone(worker.poll())
