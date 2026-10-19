"""Public BFS contract on finite callback fixtures, without game rules."""

import json
import unittest
from copy import deepcopy
from dataclasses import replace
from unittest.mock import Mock, patch

from src.solvers.bfs import solver as bfs
from src.solvers.common.result import SolverMetrics
from tests.solvers.test_TV4_runtime import FakeState, FakeSuccessor, fake_key


class TestTV4BFSContract(unittest.TestCase):
    def setUp(self):
        self.tracer = self.enterContext(patch("src.solvers.common.runtime.tracemalloc"))
        self.tracer.is_tracing.return_value = False
        self.tracer.get_traced_memory.return_value = (100, 900)
        self.enterContext(patch("src.solvers.common.runtime.perf_counter", return_value=0))
        self.start = FakeState("SPLIT", ((1, 1), (3, 3)), 0, (True, False))
        self.closed = replace(self.start, bridges=(False, False))
        self.opened = replace(self.start, bridges=(False, True))
        self.switched = replace(self.opened, active=1)
        self.goal = FakeState("UPRIGHT", ((4, 4),), bridges=(False, True))
        self.graph = {
            fake_key(self.start): [FakeSuccessor("UP", self.closed),
                                   FakeSuccessor("RIGHT", self.opened, 3)],
            fake_key(self.closed): [FakeSuccessor("LEFT", self.closed)],
            fake_key(self.opened): [FakeSuccessor("SWITCH", self.switched)],
            fake_key(self.switched): [FakeSuccessor("DOWN", self.goal, 2)],
            fake_key(self.goal): [],
        }
        self.args = dict(
            game_map=self.graph, start_state=self.start, map_id="snapshot_fixture",
            bridge_ids=("b01", "b02"), state_key=fake_key,
            is_goal=lambda _, state: state == self.goal,
            successors=lambda graph, state: graph[fake_key(state)],
            validate_start_state=self.validate_start,
        )

    @staticmethod
    def validate_start(graph, state):
        if fake_key(state) not in graph:
            raise ValueError("snapshot is not in the fixture graph")

    def test_legacy_entry_point_is_the_same_callable(self):
        self.assertIs(bfs.solve_bfs, bfs._solve_bfs)

    def test_required_callbacks_and_metadata_have_no_fallback(self):
        for name in ("map_id", "bridge_ids", "state_key", "is_goal",
                     "successors", "validate_start_state"):
            with self.subTest(missing=name):
                args = {key: value for key, value in self.args.items() if key != name}
                with self.assertRaisesRegex(TypeError, name):
                    bfs.solve_bfs(**args)
        self.tracer.start.assert_not_called()

    def test_snapshot_route_keeps_bridge_and_active_branches_and_round_trips(self):
        before = deepcopy((self.graph, self.start))
        result = bfs.solve_bfs(**self.args)
        payload = json.loads(json.dumps(result.to_dict(), allow_nan=False))
        self.assertEqual(result.status, "SOLVED")
        self.assertEqual(result.actions, ["RIGHT", "SWITCH", "DOWN"])
        self.assertEqual(result.metrics.solution_length, 3)
        self.assertEqual(result.metrics.solution_cost, 6)
        self.assertEqual(result.metrics.expanded_nodes, 4)
        snapshot = payload["start_state"]
        restored = FakeState(
            snapshot["mode"], tuple(tuple(cell) for cell in snapshot["cells"]),
            snapshot["active"],
            tuple(snapshot["bridges"][bid] for bid in self.args["bridge_ids"]),
        )
        self.assertEqual(fake_key(restored), fake_key(self.start))
        replayed = bfs.solve_bfs(**{**self.args, "start_state": restored})
        self.assertEqual(replayed.actions, result.actions)
        self.assertEqual(replayed.metrics, result.metrics)
        self.assertEqual((self.graph, self.start), before)
        self.assertEqual(self.tracer.stop.call_count, 2)

    def test_validator_rejects_snapshot_with_same_geometry_but_wrong_bridges(self):
        invalid = replace(self.start, bridges=(True, True))
        goal = Mock(return_value=True)
        result = bfs.solve_bfs(**{**self.args, "start_state": invalid, "is_goal": goal})
        self.assertEqual(result.status, "ERROR")
        self.assertIn("ValueError: snapshot is not in the fixture graph", result.error)
        self.assertIsNone(result.start_state)
        self.assertEqual(result.metrics, SolverMetrics())
        json.dumps(result.to_dict(), allow_nan=False)
        goal.assert_not_called()
        self.tracer.start.assert_not_called()

    def test_invalid_bridge_metadata_is_error_even_for_goal_snapshot(self):
        for ids in (None, (), ("b01",), ("b02", "b01"), ("b01", "b01"),
                    ("", "b02"), (1, 2)):
            with self.subTest(bridge_ids=ids):
                result = bfs.solve_bfs(**{
                    **self.args, "start_state": self.goal, "bridge_ids": ids,
                })
                self.assertEqual(result.status, "ERROR")
                self.assertIsNone(result.start_state)
                self.assertEqual(result.metrics, SolverMetrics())
                json.dumps(result.to_dict(), allow_nan=False)
        self.tracer.start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
