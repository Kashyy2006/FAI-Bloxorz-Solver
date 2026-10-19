import json
import tracemalloc
import unittest
from copy import deepcopy
from dataclasses import dataclass, replace
from threading import Event
from unittest.mock import Mock, call, patch

from src.solvers.common.result import SolverMetrics
from src.solvers.dfs import solver as dfs


@dataclass(frozen=True)
class FakeState:
    mode: str
    cells: tuple[tuple[int, int], ...]
    active: int | None = None
    bridges: tuple[bool, ...] = ()


@dataclass(frozen=True)
class FakeSuccessor:
    action: str
    state: FakeState
    cost: int = 1


def fake_key(state):
    return state.mode, state.cells, state.active, state.bridges


class TestTV4DFSResult(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.clock = self.enterContext(patch(
            "src.solvers.common.runtime.perf_counter", side_effect=lambda: self.now,
        ))
        self.tracer = self.enterContext(patch("src.solvers.common.runtime.tracemalloc"))
        self.tracer.is_tracing.return_value = False
        self.tracer.get_traced_memory.return_value = (100, 900)
        self.s, self.a, self.b, self.c, self.g = (
            FakeState("UPRIGHT", ((0, col),)) for col in range(5)
        )
        self.graph = {
            fake_key(self.s): [FakeSuccessor("UP", self.a, 3), FakeSuccessor("DOWN", self.b)],
            fake_key(self.a): [FakeSuccessor("RIGHT", self.c)],
            fake_key(self.c): [FakeSuccessor("DOWN", self.g)],
            fake_key(self.b): [FakeSuccessor("RIGHT", self.g)],
        }
        self.validator = Mock()

    def successors(self, game_map, state):
        self.now += 0.125
        return game_map.get(fake_key(state), [])

    def solve(self, **overrides):
        args = dict(
            game_map=self.graph, start_state=self.s, map_id="fake_graph",
            bridge_ids=(), state_key=fake_key,
            is_goal=lambda _, state: fake_key(state) == fake_key(self.g),
            successors=self.successors, validate_start_state=self.validator,
        )
        args.update(overrides)
        return dfs.solve_dfs(**args)

    def payload(self, result, status):
        payload = json.loads(json.dumps(result.to_dict(), allow_nan=False))
        self.assertEqual(payload["status"], status)
        self.assertEqual(set(payload), {
            "schema_version", "map_id", "algorithm", "status", "start_state",
            "actions", "metrics", "timeout_s", "cost_model", "heuristic", "error",
        })
        self.assertEqual(set(payload["metrics"]), {
            "search_time_s", "peak_memory_bytes", "expanded_nodes",
            "solution_length", "solution_cost",
        })
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["algorithm"], "DFS")
        self.assertEqual(payload["cost_model"], "base1_fragile2_switch1_v1")
        self.assertIsNone(payload["heuristic"])
        if status != "SOLVED":
            self.assertIsNone(payload["actions"])
            self.assertIsNone(payload["metrics"]["solution_length"])
            self.assertIsNone(payload["metrics"]["solution_cost"])
        if status == "ERROR":
            self.assertTrue(payload["error"].strip())
        else:
            self.assertIsNone(payload["error"])
        return payload

    def test_solved_metrics_cost_and_independent_snapshot(self):
        before = deepcopy((self.graph, self.s))
        result = self.solve()
        payload = self.payload(result, "SOLVED")
        self.assertEqual(payload["actions"], ["UP", "RIGHT", "DOWN"])
        self.assertEqual(payload["metrics"], dict(
            search_time_s=0.375, peak_memory_bytes=900, expanded_nodes=3,
            solution_length=3, solution_cost=5,
        ))
        self.validator.assert_called_once_with(self.graph, self.s)
        self.assertEqual((self.graph, self.s), before)
        payload["start_state"]["cells"][0][0] = 99
        self.assertEqual(result.start_state["cells"], [[0, 0]])
        self.tracer.stop.assert_called_once()

    def test_unsolvable_keeps_measured_statistics(self):
        result = self.solve(game_map={})
        self.payload(result, "UNSOLVABLE")
        self.assertEqual(result.metrics.expanded_nodes, 1)
        self.assertEqual(result.metrics.search_time_s, 0.125)
        self.assertEqual(result.metrics.peak_memory_bytes, 900)

    def test_valid_goal_wins_over_cancellation_without_search(self):
        event = Event()
        event.set()
        key, successors = Mock(), Mock()
        result = self.solve(start_state=self.g, state_key=key,
                            successors=successors, cancel_event=event)
        payload = self.payload(result, "SOLVED")
        self.assertEqual(payload["actions"], [])
        self.assertEqual(result.metrics, SolverMetrics(solution_length=0, solution_cost=0))
        self.validator.assert_called_once_with(self.graph, self.g)
        key.assert_not_called()
        successors.assert_not_called()
        self.assertEqual(self.tracer.mock_calls, [])

    def test_invalid_timeout_is_error_before_goal_or_search(self):
        for timeout in (0, -1, True, False, "60", None, float("nan"),
                        float("inf"), -float("inf"), 10 ** 1000):
            with self.subTest(value_type=type(timeout).__name__):
                goal = Mock(return_value=True)
                result = self.solve(timeout_s=timeout, is_goal=goal)
                payload = self.payload(result, "ERROR")
                self.assertEqual(payload["map_id"], "fake_graph")
                self.assertIsNone(payload["timeout_s"])
                self.assertIsNone(payload["start_state"])
                self.assertIn("timeout_s", payload["error"])
                self.assertEqual(result.metrics, SolverMetrics())
                goal.assert_not_called()
        self.tracer.start.assert_not_called()

    def test_invalid_map_id_event_and_callbacks_are_pre_search_errors(self):
        cases = [("map_id", value) for value in (None, [], " ")]
        cases += [("cancel_event", object()), ("cancel_event", Mock(is_set=1))]
        cases += [(name, None) for name in (
            "state_key", "is_goal", "successors", "validate_start_state",
        )]
        for name, value in cases:
            with self.subTest(field=name, value=value):
                result = self.solve(**{name: value})
                payload = self.payload(result, "ERROR")
                self.assertIn(name, payload["error"])
                self.assertEqual(result.metrics, SolverMetrics())
                if name == "map_id":
                    self.assertIsNone(payload["map_id"])
        self.tracer.start.assert_not_called()

    def test_validator_and_snapshot_errors_precede_goal(self):
        cases = (
            dict(validate_start_state=Mock(side_effect=ValueError("invalid state"))),
            dict(start_state=object()),
            dict(start_state=replace(self.s, bridges=(False,))),
            dict(start_state=replace(self.s, cells=((float("nan"), 0),))),
            dict(start_state=replace(self.s, bridges=(False, True)), bridge_ids=("b2", "b1")),
        )
        for overrides in cases:
            with self.subTest(field=next(iter(overrides))):
                goal = Mock(return_value=True)
                result = self.solve(is_goal=goal, **overrides)
                payload = self.payload(result, "ERROR")
                self.assertIsNone(payload["start_state"])
                self.assertIn("start_state", payload["error"])
                self.assertEqual(payload["timeout_s"], 60)
                self.assertEqual(result.metrics, SolverMetrics())
                goal.assert_not_called()
        self.tracer.start.assert_not_called()

    def test_current_split_snapshot_and_bridges_round_trip(self):
        state = FakeState("SPLIT", ((1, 1), (3, 3)), 1, (False, True))
        result = self.solve(start_state=state, bridge_ids=("b1", "b2"), game_map={})
        snapshot = self.payload(result, "UNSOLVABLE")["start_state"]
        self.assertEqual(snapshot, dict(mode="SPLIT", cells=[[1, 1], [3, 3]], active=1,
                                       bridges={"b1": False, "b2": True}))
        restored = FakeState(snapshot["mode"], tuple(map(tuple, snapshot["cells"])),
                             snapshot["active"], tuple(snapshot["bridges"][i] for i in ("b1", "b2")))
        self.assertEqual(fake_key(restored), fake_key(state))

    def test_validation_serialization_and_path_building_are_outside_timer(self):
        def validate(*_):
            self.tracer.start.assert_not_called()
            self.now += 10

        def key(state):
            self.tracer.start.assert_called_once()
            return fake_key(state)

        original_path = dfs.reconstruct_actions
        original_to_dict = dfs.SolverResult.to_dict

        def build_path(*args):
            self.now += 5
            return original_path(*args)

        def serialize(result):
            self.tracer.stop.assert_called_once()
            self.now += 20
            return original_to_dict(result)

        with patch.object(dfs, "reconstruct_actions", side_effect=build_path), \
                patch.object(dfs.SolverResult, "to_dict", serialize):
            result = self.solve(validate_start_state=validate, state_key=key)
        self.payload(result, "SOLVED")
        self.assertEqual(result.metrics.search_time_s, 0.375)

    def test_cancel_before_search_does_not_compute_key_or_expand(self):
        event = Event()
        event.set()
        key, successors = Mock(), Mock()
        result = self.solve(cancel_event=event, state_key=key, successors=successors)
        self.payload(result, "CANCELLED")
        self.assertEqual(result.metrics.expanded_nodes, 0)
        key.assert_not_called()
        successors.assert_not_called()
        self.tracer.stop.assert_called_once()

    def test_exact_deadline_before_first_pop(self):
        def key(state):
            self.now = 60
            return fake_key(state)

        result = self.solve(state_key=key)
        self.payload(result, "TIMEOUT")
        self.assertEqual(result.metrics.expanded_nodes, 0)
        self.assertEqual(result.metrics.search_time_s, 60)
        self.tracer.stop.assert_called_once()

    def test_stop_after_empty_successors_preserves_expansion(self):
        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                self.now = 0
                event = Event()

                def successors(*_):
                    self.now = 60
                    if cancel:
                        event.set()
                    return []

                result = self.solve(successors=successors, cancel_event=event)
                self.payload(result, "CANCELLED" if cancel else "TIMEOUT")
                self.assertEqual(result.metrics.expanded_nodes, 1)
                self.assertEqual(result.metrics.search_time_s, 60)

    def test_guard_runs_between_duplicate_successors(self):
        event = Event()
        calls = []

        def key(state):
            calls.append(state)
            if len(calls) == 3:
                event.set()
            return fake_key(state)

        duplicates = [FakeSuccessor("UP", self.s), FakeSuccessor("DOWN", replace(self.s))]
        result = self.solve(state_key=key, cancel_event=event, successors=lambda *_: duplicates)
        self.payload(result, "CANCELLED")
        self.assertEqual(len(calls), 3)
        self.assertEqual(result.metrics.expanded_nodes, 1)
        self.tracer.stop.assert_called_once()

    def test_terminal_goal_callback_cannot_override_stop(self):
        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                self.now = 0
                event = Event()

                def goal(_, state):
                    if state == self.g:
                        self.now = 60
                        if cancel:
                            event.set()
                        return True
                    return False

                result = self.solve(is_goal=goal, cancel_event=event)
                self.payload(result, "CANCELLED" if cancel else "TIMEOUT")
                self.assertEqual(result.metrics.expanded_nodes, 3)

    def test_callback_errors_are_errors_not_unsolvable(self):
        for name in ("state_key", "is_goal", "successors"):
            with self.subTest(callback=name):
                result = self.solve(**{name: Mock(side_effect=ValueError("callback failed"))})
                self.payload(result, "ERROR")
                self.assertIn("ValueError: callback failed", result.error)
                self.assertEqual(result.metrics.expanded_nodes, int(name == "successors"))

    def test_error_during_second_expansion_keeps_progress(self):
        def successors(game_map, state):
            edges = self.successors(game_map, state)
            if state == self.a:
                raise ValueError("second expansion failed")
            return edges

        result = self.solve(successors=successors)
        self.payload(result, "ERROR")
        self.assertEqual(result.metrics.expanded_nodes, 2)
        self.assertEqual(result.metrics.search_time_s, 0.25)
        self.assertEqual(result.metrics.peak_memory_bytes, 900)

    def test_event_callback_error_keeps_progress(self):
        event = Mock()

        def successors(game_map, state):
            edges = self.successors(game_map, state)
            event.is_set.side_effect = RuntimeError("event failed")
            return edges

        event.is_set.return_value = False
        result = self.solve(cancel_event=event, successors=successors)
        self.payload(result, "ERROR")
        self.assertIn("event failed", result.error)
        self.assertEqual(result.metrics.expanded_nodes, 1)

    def test_path_failure_cleans_up_after_timer_stopped(self):
        def fail_path(*_):
            self.now += 5
            raise ValueError("bad parent")

        with patch.object(dfs, "reconstruct_actions", side_effect=fail_path):
            result = self.solve()
        self.payload(result, "ERROR")
        self.assertIn("bad parent", result.error)
        self.assertEqual(result.metrics.search_time_s, 0.375)
        self.assertEqual(result.metrics.expanded_nodes, 3)
        self.tracer.stop.assert_called_once()

    def test_result_serialization_failure_is_error_after_cleanup(self):
        with patch.object(dfs.SolverResult, "to_dict", side_effect=ValueError("bad result")):
            result = self.solve()
        self.payload(result, "ERROR")
        self.assertIn("bad result", result.error)
        self.tracer.stop.assert_called_once()

    def test_cleanup_failure_keeps_original_error_and_clears_solved_path(self):
        self.tracer.get_traced_memory.side_effect = RuntimeError("peak failed")
        for overrides in ({"successors": Mock(side_effect=ValueError("engine failed"))}, {}):
            with self.subTest(overrides=bool(overrides)):
                result = self.solve(**overrides)
                self.payload(result, "ERROR")
                self.assertIn("peak failed", result.error)
                if overrides:
                    self.assertIn("engine failed", result.error)
        self.assertEqual(self.tracer.stop.call_count, 2)

    def test_external_tracing_is_never_reset_or_stopped(self):
        self.tracer.is_tracing.return_value = True
        result = self.solve()
        self.payload(result, "ERROR")
        self.assertEqual(result.metrics, SolverMetrics())
        self.assertEqual(self.tracer.mock_calls, [call.is_tracing()])

    def test_interrupts_propagate_after_cleanup(self):
        for exception in (KeyboardInterrupt, SystemExit):
            with self.subTest(exception=exception.__name__):
                with self.assertRaises(exception):
                    self.solve(successors=Mock(side_effect=exception))
        self.assertEqual(self.tracer.stop.call_count, 2)


class TestTV4DFSRealTracing(unittest.TestCase):
    def solve(self, **overrides):
        args = dict(
            game_map={}, start_state=FakeState("UPRIGHT", ((0, 0),)),
            map_id="fake_graph", bridge_ids=(), state_key=fake_key,
            is_goal=lambda *_: False, successors=lambda *_: [],
            validate_start_state=lambda *_: None,
        )
        args.update(overrides)
        return dfs.solve_dfs(**args)

    def test_repeated_solves_release_real_tracing(self):
        self.assertFalse(tracemalloc.is_tracing())
        for _ in range(2):
            result = self.solve()
            self.assertEqual(result.status, "UNSOLVABLE")
            self.assertEqual(result.metrics.expanded_nodes, 1)
            self.assertGreaterEqual(result.metrics.search_time_s, 0)
            self.assertIs(type(result.metrics.peak_memory_bytes), int)
            self.assertGreater(result.metrics.peak_memory_bytes, 0)
            json.dumps(result.to_dict(), allow_nan=False)
            self.assertFalse(tracemalloc.is_tracing())

    def test_error_releases_real_tracing(self):
        self.assertFalse(tracemalloc.is_tracing())
        result = self.solve(successors=Mock(side_effect=ValueError("callback failed")))
        self.assertEqual(result.status, "ERROR")
        self.assertEqual(result.metrics.expanded_nodes, 1)
        self.assertGreater(result.metrics.peak_memory_bytes, 0)
        self.assertFalse(tracemalloc.is_tracing())

    def test_external_real_tracing_survives_solve(self):
        self.assertFalse(tracemalloc.is_tracing())
        tracemalloc.start()
        try:
            allocation = bytearray(256 * 1024)
            del allocation
            peak = tracemalloc.get_traced_memory()[1]
            result = self.solve()
            self.assertEqual(result.status, "ERROR")
            self.assertEqual(result.metrics, SolverMetrics())
            self.assertTrue(tracemalloc.is_tracing())
            self.assertGreaterEqual(tracemalloc.get_traced_memory()[1], peak)
        finally:
            tracemalloc.stop()


if __name__ == "__main__":
    unittest.main()
