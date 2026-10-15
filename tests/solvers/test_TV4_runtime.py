import json
import unittest
from copy import deepcopy
from dataclasses import dataclass, replace
from threading import Event
from unittest.mock import Mock, call, patch

from src.solvers.common.result import SolverMetrics
from src.solvers.common.runtime import SearchRuntime, SearchStopped, validate_timeout
from src.solvers.bfs import solver as bfs


class TestTV4Runtime(unittest.TestCase):
    def setUp(self):
        self.now = 10.0
        self.clock = patch(
            "src.solvers.common.runtime.perf_counter", side_effect=lambda: self.now,
        ).start()
        self.tracer = patch("src.solvers.common.runtime.tracemalloc").start()
        self.tracer.is_tracing.return_value = False
        self.tracer.get_traced_memory.return_value = (100, 900)
        self.addCleanup(patch.stopall)

    def test_timeout_validation(self):
        for value in (60, 0.5):
            self.assertEqual(validate_timeout(value), float(value))
        for value in (0, -1, True, False, "60", None, float("nan"),
                      float("inf"), -float("inf"), 10 ** 1000):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaisesRegex(ValueError, "timeout_s"):
                    validate_timeout(value)

    def test_invalid_event_is_rejected_before_measurement(self):
        for event in (object(), Mock(is_set=False)):
            with self.subTest(event=event):
                with self.assertRaisesRegex(ValueError, "cancel_event"):
                    SearchRuntime(60, event)
        self.tracer.start.assert_not_called()

    def test_cancel_precedes_exact_deadline(self):
        event = Event()
        runtime = SearchRuntime(2, event)
        runtime.start()
        self.now = 12
        event.set()
        with self.assertRaises(SearchStopped) as stopped:
            runtime.check_stop()
        self.assertEqual(stopped.exception.status, "CANCELLED")
        event.clear()
        with self.assertRaises(SearchStopped) as stopped:
            runtime.check_stop()
        self.assertEqual(stopped.exception.status, "TIMEOUT")
        runtime.finish()

    def test_clock_and_peak_have_separate_stop_points(self):
        metrics = SolverMetrics(expanded_nodes=3)
        runtime = SearchRuntime(60, metrics=metrics)
        runtime.start()
        self.now = 10.25
        runtime.mark_search_stopped()
        self.now = 15
        runtime.finish()
        runtime.finish()
        runtime.mark_search_stopped()
        self.assertEqual(metrics.search_time_s, 0.25)
        self.assertEqual(metrics.peak_memory_bytes, 900)
        self.assertEqual(metrics.expanded_nodes, 3)
        self.assertEqual(self.tracer.mock_calls, [
            call.is_tracing(), call.start(), call.get_traced_memory(), call.stop(),
        ])

    def test_finish_without_start_has_zero_metrics_and_no_tracer_calls(self):
        runtime = SearchRuntime()
        runtime.finish()
        self.assertEqual(runtime.metrics, SolverMetrics())
        self.assertEqual(self.tracer.mock_calls, [])

    def test_existing_trace_is_not_reset_or_stopped(self):
        self.tracer.is_tracing.return_value = True
        runtime = SearchRuntime()
        with self.assertRaisesRegex(RuntimeError, "tracemalloc"):
            runtime.start()
        runtime.finish()
        self.assertEqual(self.tracer.mock_calls, [call.is_tracing()])
        self.assertEqual(runtime.metrics, SolverMetrics())

    def test_peak_failure_still_stops_owned_trace(self):
        runtime = SearchRuntime()
        runtime.start()
        self.tracer.get_traced_memory.side_effect = RuntimeError("peak failed")
        with self.assertRaisesRegex(RuntimeError, "peak failed"):
            runtime.finish()
        runtime.finish()
        self.tracer.stop.assert_called_once()

    def test_clock_failure_after_trace_start_still_cleans_up(self):
        runtime = SearchRuntime()
        self.clock.side_effect = RuntimeError("clock failed")
        with self.assertRaisesRegex(RuntimeError, "clock failed"):
            runtime.start()
        runtime.finish()
        self.tracer.stop.assert_called_once()


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
    return (state.mode, state.cells, state.active, state.bridges)


class TestTV4BFSResult(unittest.TestCase):
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
            fake_key(self.s): [FakeSuccessor("UP", self.a, 3),
                               FakeSuccessor("DOWN", self.b)],
            fake_key(self.a): [FakeSuccessor("RIGHT", self.g, 3)],
            fake_key(self.b): [FakeSuccessor("DOWN", self.c)],
            fake_key(self.c): [FakeSuccessor("RIGHT", self.g)],
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
        return bfs._solve_bfs(**args)

    def payload(self, result, status):
        payload = json.loads(json.dumps(result.to_dict(), allow_nan=False))
        self.assertEqual(payload["status"], status)
        self.assertEqual(set(payload), {
            "schema_version", "map_id", "algorithm", "status", "start_state",
            "actions", "metrics", "timeout_s", "cost_model", "heuristic", "error",
        })
        self.assertEqual(len(payload["metrics"]), 5)
        self.assertEqual(payload["algorithm"], "BFS")
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

    def test_solved_bfs_metrics_cost_and_immutable_inputs(self):
        before = deepcopy((self.graph, self.s))
        result = self.solve()
        payload = self.payload(result, "SOLVED")
        self.assertEqual(payload["actions"], ["UP", "RIGHT"])
        self.assertEqual(payload["metrics"], dict(
            search_time_s=0.375, peak_memory_bytes=900, expanded_nodes=3,
            solution_length=2, solution_cost=6,
        ))
        self.validator.assert_called_once_with(self.graph, self.s)
        self.assertEqual((self.graph, self.s), before)
        payload["start_state"]["cells"][0][0] = 99
        self.assertEqual(result.start_state["cells"], [[0, 0]])
        self.tracer.stop.assert_called_once()

    def test_validation_and_serialization_are_outside_measurement(self):
        def validate(*_):
            self.tracer.start.assert_not_called()
            self.now += 10

        original_to_dict = bfs.SolverResult.to_dict

        def serialize(result):
            self.tracer.stop.assert_called_once()
            self.now += 20
            return original_to_dict(result)

        def key(state):
            self.tracer.start.assert_called_once()
            return fake_key(state)

        with patch.object(bfs.SolverResult, "to_dict", serialize):
            result = self.solve(validate_start_state=validate, state_key=key)
        self.payload(result, "SOLVED")
        self.assertEqual(result.metrics.search_time_s, 0.375)

    def test_unsolvable_preserves_statistics(self):
        payload = self.payload(self.solve(game_map={}), "UNSOLVABLE")
        self.assertEqual(payload["metrics"]["expanded_nodes"], 1)
        self.assertEqual(payload["metrics"]["search_time_s"], 0.125)
        self.assertEqual(payload["metrics"]["peak_memory_bytes"], 900)

    def test_already_solved_after_validation_wins_over_cancellation(self):
        event = Event()
        event.set()
        key, successors = Mock(), Mock()
        with patch.object(bfs, "deque") as queue:
            result = self.solve(start_state=self.g, state_key=key,
                                successors=successors, cancel_event=event)
        payload = self.payload(result, "SOLVED")
        self.assertEqual(payload["actions"], [])
        self.assertEqual(payload["metrics"], dict(
            search_time_s=0, peak_memory_bytes=0, expanded_nodes=0,
            solution_length=0, solution_cost=0,
        ))
        self.validator.assert_called_once_with(self.graph, self.g)
        queue.assert_not_called()
        key.assert_not_called()
        successors.assert_not_called()
        self.tracer.start.assert_not_called()

    def test_invalid_timeout_returns_serializable_error_without_search(self):
        for timeout in (0, -1, True, "60", None, float("nan"),
                        float("inf"), -float("inf"), 10 ** 1000):
            with self.subTest(value_type=type(timeout).__name__):
                with patch.object(bfs, "deque") as queue:
                    result = self.solve(timeout_s=timeout, start_state=self.g)
                payload = self.payload(result, "ERROR")
                self.assertIsNone(payload["timeout_s"])
                self.assertIn("timeout_s", payload["error"])
                self.assertEqual(result.metrics, SolverMetrics())
                queue.assert_not_called()
        self.tracer.start.assert_not_called()

    def test_invalid_map_id_and_event_return_errors(self):
        for overrides in ({"map_id": None}, {"map_id": []}, {"map_id": " "},
                          {"cancel_event": object()}, {"cancel_event": Mock(is_set=1)}):
            with self.subTest(field=next(iter(overrides))):
                result = self.solve(**overrides)
                self.payload(result, "ERROR")
                self.assertEqual(result.metrics, SolverMetrics())
        self.tracer.start.assert_not_called()

    def test_validator_and_snapshot_errors_precede_search(self):
        for overrides in (
            {"validate_start_state": Mock(side_effect=ValueError("invalid snapshot"))},
            {"start_state": object()},
            {"start_state": replace(self.s, bridges=(False,))},
            {"start_state": replace(self.s, cells=((float("nan"), 0),))},
        ):
            with self.subTest(field=next(iter(overrides))):
                result = self.solve(**overrides)
                payload = self.payload(result, "ERROR")
                self.assertIsNone(payload["start_state"])
                self.assertIn("start_state", payload["error"])
                self.assertEqual(result.metrics, SolverMetrics())
        self.tracer.start.assert_not_called()

    def test_invalid_callbacks_are_rejected_before_measurement(self):
        for name in ("state_key", "is_goal", "successors", "validate_start_state"):
            with self.subTest(callback=name):
                result = self.solve(**{name: None})
                payload = self.payload(result, "ERROR")
                self.assertIn(name, payload["error"])
                self.assertEqual(result.metrics, SolverMetrics())

    def test_cancelled_before_expansion_cleans_up(self):
        event = Event()
        event.set()
        result = self.solve(cancel_event=event)
        self.payload(result, "CANCELLED")
        self.assertEqual(result.metrics.expanded_nodes, 0)
        self.assertEqual(result.metrics.peak_memory_bytes, 900)
        self.tracer.stop.assert_called_once()

    def test_timeout_at_exact_deadline(self):
        self.clock.side_effect = [0, 60, 60]
        result = self.solve()
        self.payload(result, "TIMEOUT")
        self.assertEqual(result.metrics.expanded_nodes, 0)
        self.assertEqual(result.metrics.search_time_s, 60)
        self.tracer.stop.assert_called_once()

    def test_mid_search_cancel_wins_over_timeout_and_keeps_expansions(self):
        event = Event()

        def successors(*_):
            event.set()
            self.now = 60
            return []

        result = self.solve(cancel_event=event, successors=successors)
        self.payload(result, "CANCELLED")
        self.assertEqual(result.metrics.expanded_nodes, 1)
        self.assertEqual(result.metrics.search_time_s, 60)
        self.tracer.stop.assert_called_once()

    def test_event_callback_errors_keep_progress(self):
        event = Mock()
        event.is_set.side_effect = [False, False, False, RuntimeError("event failed")]
        result = self.solve(cancel_event=event)
        self.payload(result, "ERROR")
        self.assertIn("event failed", result.error)
        self.assertEqual(result.metrics.expanded_nodes, 1)
        self.tracer.stop.assert_called_once()

    def test_engine_callback_errors_are_errors_not_unsolvable(self):
        for name in ("state_key", "is_goal", "successors"):
            with self.subTest(callback=name):
                result = self.solve(**{name: Mock(side_effect=RuntimeError("engine failed"))})
                self.payload(result, "ERROR")
                self.assertIn("RuntimeError: engine failed", result.error)
                self.assertEqual(result.metrics.expanded_nodes, int(name == "successors"))

    def test_failure_after_prior_expansion_keeps_both_calls(self):
        def successors(game_map, state):
            self.now += 0.125
            if state == self.a:
                raise ValueError("second expansion failed")
            return game_map.get(fake_key(state), [])

        result = self.solve(successors=successors)
        self.payload(result, "ERROR")
        self.assertEqual(result.metrics.expanded_nodes, 2)
        self.assertEqual(result.metrics.search_time_s, 0.25)
        self.assertEqual(result.metrics.peak_memory_bytes, 900)

    def test_path_reconstruction_is_outside_search_time_and_error_cleans_up(self):
        def fail_path(*_):
            self.now += 5
            raise ValueError("bad parent")

        with patch.object(bfs, "reconstruct_actions", side_effect=fail_path):
            result = self.solve()
        self.payload(result, "ERROR")
        self.assertIn("bad parent", result.error)
        self.assertEqual(result.metrics.search_time_s, 0.375)
        self.assertEqual(result.metrics.expanded_nodes, 3)
        self.tracer.stop.assert_called_once()

    def test_serialization_error_is_reported_after_cleanup(self):
        with patch.object(bfs.SolverResult, "to_dict", side_effect=ValueError("bad result")):
            result = self.solve()
        self.payload(result, "ERROR")
        self.assertIn("bad result", result.error)
        self.assertEqual(result.metrics.expanded_nodes, 3)
        self.tracer.stop.assert_called_once()

    def test_cleanup_error_does_not_hide_engine_error(self):
        self.tracer.get_traced_memory.side_effect = RuntimeError("peak failed")
        result = self.solve(successors=Mock(side_effect=ValueError("engine failed")))
        self.payload(result, "ERROR")
        self.assertIn("engine failed", result.error)
        self.assertIn("peak failed", result.error)
        self.assertEqual(result.metrics.expanded_nodes, 1)
        self.tracer.stop.assert_called_once()

    def test_existing_trace_returns_error_without_touching_external_session(self):
        self.tracer.is_tracing.return_value = True
        with patch.object(bfs, "deque") as queue:
            result = self.solve()
        self.payload(result, "ERROR")
        self.assertEqual(result.metrics, SolverMetrics())
        self.assertEqual(self.tracer.mock_calls, [call.is_tracing()])
        queue.assert_not_called()

    def test_keyboard_interrupt_propagates_but_cleans_up(self):
        with self.assertRaises(KeyboardInterrupt):
            self.solve(successors=Mock(side_effect=KeyboardInterrupt))
        self.tracer.stop.assert_called_once()

    def test_snapshot_preserves_current_split_and_bridge_state(self):
        state = FakeState("SPLIT", ((1, 1), (3, 3)), 1, (False, True))
        result = self.solve(start_state=state, bridge_ids=("b1", "b2"), game_map={})
        payload = self.payload(result, "UNSOLVABLE")
        self.assertEqual(payload["start_state"], dict(
            mode="SPLIT", cells=[[1, 1], [3, 3]], active=1,
            bridges={"b1": False, "b2": True},
        ))


class TestTV4RealTracing(unittest.TestCase):
    def test_repeated_solves_use_and_release_real_tracing(self):
        import tracemalloc

        self.assertFalse(tracemalloc.is_tracing(), "Run this smoke test without an external profiler")
        state = FakeState("UPRIGHT", ((0, 0),))
        for _ in range(2):
            result = bfs._solve_bfs(
                {}, state, map_id="fake_graph", bridge_ids=(), state_key=fake_key,
                is_goal=lambda *_: False, successors=lambda *_: [],
                validate_start_state=lambda *_: None,
            )
            self.assertEqual(result.status, "UNSOLVABLE")
            self.assertEqual(result.metrics.expanded_nodes, 1)
            self.assertGreaterEqual(result.metrics.search_time_s, 0)
            self.assertIs(type(result.metrics.peak_memory_bytes), int)
            self.assertGreater(result.metrics.peak_memory_bytes, 0)
            json.dumps(result.to_dict(), allow_nan=False)
            self.assertFalse(tracemalloc.is_tracing())

    def test_real_tracing_is_released_after_engine_error(self):
        import tracemalloc

        self.assertFalse(tracemalloc.is_tracing())
        result = bfs._solve_bfs(
            {}, FakeState("UPRIGHT", ((0, 0),)), map_id="fake_graph", bridge_ids=(),
            state_key=fake_key, is_goal=lambda *_: False,
            successors=Mock(side_effect=ValueError("engine failed")),
            validate_start_state=lambda *_: None,
        )
        self.assertEqual(result.status, "ERROR")
        self.assertEqual(result.metrics.expanded_nodes, 1)
        self.assertGreater(result.metrics.peak_memory_bytes, 0)
        self.assertFalse(tracemalloc.is_tracing())

    def test_real_external_tracing_and_its_peak_survive_solve(self):
        import tracemalloc

        self.assertFalse(tracemalloc.is_tracing())
        tracemalloc.start()
        try:
            allocation = bytearray(256 * 1024)
            del allocation
            previous_peak = tracemalloc.get_traced_memory()[1]
            result = bfs._solve_bfs(
                {}, FakeState("UPRIGHT", ((0, 0),)), map_id="fake_graph", bridge_ids=(),
                state_key=fake_key, is_goal=lambda *_: False, successors=lambda *_: [],
                validate_start_state=lambda *_: None,
            )
            self.assertEqual(result.status, "ERROR")
            self.assertEqual(result.metrics, SolverMetrics())
            self.assertTrue(tracemalloc.is_tracing())
            self.assertGreaterEqual(tracemalloc.get_traced_memory()[1], previous_peak)
        finally:
            tracemalloc.stop()


if __name__ == "__main__":
    unittest.main()
