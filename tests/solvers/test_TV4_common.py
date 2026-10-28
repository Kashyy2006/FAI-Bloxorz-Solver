import json
import unittest
from dataclasses import dataclass, replace

from src.solvers.common.path import reconstruct_actions
from src.solvers.common.result import (
    SolverMetrics,
    SolverResult,
    snapshot_to_dict,
)


@dataclass(frozen=True)
class FakeState:
    mode: str
    cells: tuple[tuple[int, int], ...]
    active: int | None
    bridges: tuple[bool, ...]


def fake_key(state):
    return (state.mode, state.cells, state.active, state.bridges)


class TestTV4Common(unittest.TestCase):
    def setUp(self):
        self.start = FakeState("UPRIGHT", ((1, 1),), None, ())

    def solved_result(self):
        return SolverResult(
            map_id="basic_01",
            algorithm="BFS",
            status="SOLVED",
            start_state=snapshot_to_dict(self.start, ()),
            actions=["RIGHT", "RIGHT"],
            metrics=SolverMetrics(
                search_time_s=0.125,
                peak_memory_bytes=1024,
                expanded_nodes=2,
                solution_length=2,
                solution_cost=2,
            ),
            timeout_s=60.0,
        )

    def test_solved_result_has_exact_json_fields(self):
        payload = json.loads(json.dumps(self.solved_result().to_dict()))
        self.assertEqual(set(payload), {
            "schema_version", "map_id", "algorithm", "status",
            "start_state", "actions", "metrics", "timeout_s",
            "cost_model", "heuristic", "error",
        })
        self.assertEqual(set(payload["metrics"]), {
            "search_time_s", "peak_memory_bytes", "expanded_nodes",
            "solution_length", "solution_cost",
        })
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["cost_model"], "base1_fragile2_switch1_v1")
        self.assertEqual(payload["actions"], ["RIGHT", "RIGHT"])
        self.assertEqual(payload["metrics"]["solution_length"], 2)
        self.assertEqual(payload["metrics"]["solution_cost"], 2)
        self.assertEqual(payload["start_state"]["bridges"], {})
        self.assertIsNone(payload["heuristic"])
        self.assertIsNone(payload["error"])

    def test_all_non_solved_statuses_keep_metrics_and_null_solution(self):
        for status in ("UNSOLVABLE", "TIMEOUT", "CANCELLED", "ERROR"):
            with self.subTest(status=status):
                result = SolverResult(
                    map_id="basic_01", algorithm="DFS", status=status,
                    start_state=snapshot_to_dict(self.start, ()),
                    actions=None,
                    metrics=SolverMetrics(0.25, 2048, 7),
                    timeout_s=60.0,
                    error="Engine failure" if status == "ERROR" else None,
                )
                payload = json.loads(json.dumps(result.to_dict()))
                self.assertIsNone(payload["actions"])
                self.assertIsNone(payload["metrics"]["solution_length"])
                self.assertIsNone(payload["metrics"]["solution_cost"])
                self.assertEqual(payload["metrics"]["expanded_nodes"], 7)
                self.assertEqual(payload["metrics"]["search_time_s"], 0.25)
                self.assertEqual(payload["metrics"]["peak_memory_bytes"], 2048)
                self.assertEqual(payload["error"], result.error)

    def test_error_before_measurement_has_zero_metrics(self):
        result = SolverResult(
            map_id="basic_01", algorithm="BFS", status="ERROR",
            start_state=snapshot_to_dict(self.start, ()),
            actions=None, metrics=SolverMetrics(), timeout_s=60.0,
            error="Invalid snapshot",
        )
        metrics = result.to_dict()["metrics"]
        self.assertEqual(metrics["search_time_s"], 0.0)
        self.assertEqual(metrics["peak_memory_bytes"], 0)
        self.assertEqual(metrics["expanded_nodes"], 0)

    def test_already_solved_representation(self):
        goal = replace(self.start, cells=((1, 4),))
        result = SolverResult(
            map_id="basic_01", algorithm="BFS", status="SOLVED",
            start_state=snapshot_to_dict(goal, ()), actions=[],
            metrics=SolverMetrics(solution_length=0, solution_cost=0),
            timeout_s=60.0,
        )
        payload = result.to_dict()
        self.assertEqual(payload["actions"], [])
        self.assertEqual(payload["metrics"]["solution_length"], 0)
        self.assertEqual(payload["metrics"]["solution_cost"], 0)
        self.assertEqual(payload["metrics"]["expanded_nodes"], 0)

    def test_rejects_inconsistent_result(self):
        good = self.solved_result()
        bad_results = [
            replace(good, algorithm="GREEDY"),
            replace(good, status="UNKNOWN"),
            replace(good, heuristic="goal_indicator_v1"),
            replace(good, algorithm="ASTAR", heuristic=None),
            replace(good, actions=None),
            replace(good, metrics=replace(good.metrics, solution_length=3)),
            replace(good, metrics=replace(good.metrics, solution_cost=None)),
            replace(good, metrics=replace(good.metrics, solution_cost=1)),
            replace(good, metrics=replace(good.metrics, solution_cost=True)),
            replace(good, actions=[], metrics=SolverMetrics(
                solution_length=0, solution_cost=1
            )),
            replace(good, status="TIMEOUT"),
            replace(good, status="ERROR", actions=None,
                    metrics=SolverMetrics(), error=" "),
            replace(good, error="Should not appear on SOLVED"),
        ]
        for result in bad_results:
            with self.subTest(result=result):
                with self.assertRaises(ValueError):
                    result.to_dict()

    def test_shared_result_supports_ucs_and_astar(self):
        good = self.solved_result()
        for algorithm, heuristic in (
            ("UCS", None), ("ASTAR", "goal_indicator_v1")
        ):
            with self.subTest(algorithm=algorithm):
                payload = replace(
                    good, algorithm=algorithm, heuristic=heuristic
                ).to_dict()
                self.assertEqual(payload["algorithm"], algorithm)
                self.assertEqual(payload["heuristic"], heuristic)

    def test_error_can_represent_unvalidated_envelope_fields_as_null(self):
        result = SolverResult(
            map_id=None, algorithm="BFS", status="ERROR", start_state=None,
            actions=None, metrics=SolverMetrics(), timeout_s=None,
            error="timeout_s: invalid input",
        )
        payload = json.loads(json.dumps(result.to_dict(), allow_nan=False))
        self.assertIsNone(payload["map_id"])
        self.assertIsNone(payload["start_state"])
        self.assertIsNone(payload["timeout_s"])
        self.assertEqual(len(payload), 11)

    def test_non_error_results_require_valid_envelope_fields(self):
        good = self.solved_result()
        for fields in (
            {"map_id": None}, {"map_id": " "}, {"map_id": 1},
            {"start_state": None}, {"start_state": []},
            {"timeout_s": None}, {"timeout_s": True}, {"timeout_s": "60"},
            {"timeout_s": 0}, {"timeout_s": -1},
            {"timeout_s": float("nan")}, {"timeout_s": float("inf")},
            {"timeout_s": 10 ** 1000},
        ):
            with self.subTest(field=next(iter(fields))):
                with self.assertRaises(ValueError):
                    replace(good, **fields).to_dict()

    def test_error_does_not_allow_invalid_non_null_envelope_values(self):
        result = replace(
            self.solved_result(), status="ERROR", actions=None,
            metrics=SolverMetrics(), error="Invalid input",
        )
        for fields in ({"timeout_s": float("nan")}, {"timeout_s": 0},
                       {"map_id": []}, {"start_state": object()}):
            with self.subTest(field=next(iter(fields))):
                with self.assertRaises(ValueError):
                    replace(result, **fields).to_dict()

    def test_json_output_does_not_share_mutable_data(self):
        result = self.solved_result()
        payload = result.to_dict()
        payload["actions"].append("UP")
        payload["start_state"]["cells"][0][0] = 99
        payload["metrics"]["expanded_nodes"] = 999
        self.assertEqual(result.actions, ["RIGHT", "RIGHT"])
        self.assertEqual(result.start_state["cells"], [[1, 1]])
        self.assertEqual(result.metrics.expanded_nodes, 2)
        self.assertEqual(self.start.cells, ((1, 1),))

    def test_snapshot_round_trip_preserves_full_key(self):
        bridge_ids = ("b01", "b02")
        states = [
            FakeState("UPRIGHT", ((1, 1),), None, (False, True)),
            FakeState("HORIZONTAL", ((1, 1), (1, 2)), None, (True, False)),
            FakeState("VERTICAL", ((1, 1), (2, 1)), None, (False, False)),
            FakeState("SPLIT", ((1, 1), (3, 3)), 0, (True, False)),
            FakeState("SPLIT", ((1, 1), (3, 3)), 1, (False, True)),
        ]
        for state in states:
            with self.subTest(state=state):
                before = fake_key(state)
                payload = json.loads(json.dumps(
                    snapshot_to_dict(state, bridge_ids)
                ))
                restored = FakeState(
                    mode=payload["mode"],
                    cells=tuple(tuple(cell) for cell in payload["cells"]),
                    active=payload["active"],
                    bridges=tuple(payload["bridges"][bid] for bid in bridge_ids),
                )
                self.assertEqual(fake_key(restored), before)
                self.assertEqual(fake_key(state), before)
                self.assertEqual(payload["bridges"], {
                    "b01": state.bridges[0], "b02": state.bridges[1]
                })
                payload["cells"][0][0] = 99
                payload["bridges"]["b01"] = not state.bridges[0]
                self.assertEqual(fake_key(state), before)

    def test_snapshot_rejects_misaligned_bridges(self):
        state = replace(self.start, bridges=(False, True))
        for bridge_ids in (("b02", "b01"), ("b01",), ("b01", "b01")):
            with self.subTest(bridge_ids=bridge_ids):
                with self.assertRaises(ValueError):
                    snapshot_to_dict(state, bridge_ids)
        with self.assertRaises(ValueError):
            snapshot_to_dict(replace(state, bridges=(0, True)), ("b01", "b02"))

    def test_snapshot_rejects_empty_or_non_string_bridge_ids(self):
        state = replace(self.start, bridges=(False,))
        for bridge_id in ("", " ", 1, False, None):
            with self.subTest(bridge_id=bridge_id):
                with self.assertRaisesRegex(ValueError, "bridge_ids"):
                    snapshot_to_dict(state, (bridge_id,))

    def test_empty_path(self):
        start_key = fake_key(self.start)
        self.assertEqual(reconstruct_actions({start_key: None}, {}, start_key), [])

    def test_multi_step_path_keeps_order_and_parent_data(self):
        start_key = fake_key(self.start)
        middle = fake_key(FakeState("HORIZONTAL", ((1, 2), (1, 3)), None, ()))
        goal = fake_key(FakeState("UPRIGHT", ((1, 4),), None, ()))
        parent = {start_key: None, middle: start_key, goal: middle}
        action_to = {middle: "RIGHT", goal: "DOWN"}
        parent_before, actions_before = parent.copy(), action_to.copy()
        self.assertEqual(reconstruct_actions(parent, action_to, goal), ["RIGHT", "DOWN"])
        self.assertEqual(parent, parent_before)
        self.assertEqual(action_to, actions_before)

    def test_path_rejects_parent_cycle(self):
        a, b = ("a",), ("b",)
        with self.assertRaises(ValueError):
            reconstruct_actions({a: b, b: a}, {a: "UP", b: "DOWN"}, b)

    def test_path_fails_on_missing_parent_or_action(self):
        a, b = ("a",), ("b",)
        with self.assertRaises(KeyError):
            reconstruct_actions({a: None}, {}, b)
        with self.assertRaises(KeyError):
            reconstruct_actions({a: None, b: a}, {}, b)


if __name__ == "__main__":
    unittest.main()
