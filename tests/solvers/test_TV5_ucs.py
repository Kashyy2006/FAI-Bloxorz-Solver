import json
import unittest
from copy import deepcopy
from dataclasses import dataclass
from time import sleep
from unittest.mock import Mock
from src.engine import initial_state, is_goal, parse_map, state_key, successors
from src.solvers.ucs.solver import _search, _solve_ucs
from src.solvers.costs.calc import calculate_step_cost


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


<<<<<<< HEAD
=======
@dataclass(frozen=True)
class FakeMap:
    tiles: dict

    def tile_at(self, cell):
        return self.tiles.get(cell, "floor")

>>>>>>> origin/feature/TV5-UCS+A_star_and_cost_calc

def fake_key(state):
    return (state.mode, state.cells, state.active, state.bridges)


class TestTV5CostCalculation(unittest.TestCase):
<<<<<<< HEAD
    def test_compatibility_cost_matches_real_engine(self):
        from src.engine import parse_map, initial_state, transition, step_cost
        data = {"schema_version": 1, "id": "cost", "name": "cost", "difficulty": "easy",
                "rows": 1, "cols": 5, "grid": [["floor", "fragile", "floor", "floor", "goal"]],
                "start": [0, 0], "bridges": [], "switches": [],
                "source": {"kind": "original", "reference": "test"}}
        game_map = parse_map(data)
        before = initial_state(game_map)
        after = transition(game_map, before, "RIGHT").next_state
        self.assertEqual(calculate_step_cost(game_map, before, after, "RIGHT"), 3)
        self.assertEqual(step_cost(game_map, before, "RIGHT", after), 3)
=======
    """Kiểm thử riêng cho hàm tính chi phí bước đi (calculate_step_cost)."""

    def setUp(self):
        self.game_map = FakeMap(
            {
                (0, 1): "fragile",
                (0, 2): "fragile",
                (1, 1): "soft",
                (2, 2): "heavy",
            }
        )

    def test_switch_cost_always_one(self):
        s1 = FakeState("SPLIT", ((1, 1), (3, 3)), active=0)
        s2 = FakeState("SPLIT", ((1, 1), (3, 3)), active=1)
        cost = calculate_step_cost(self.game_map, s1, s2, "SWITCH")
        self.assertEqual(cost, 1)

    def test_normal_move_cost_is_one(self):
        s1 = FakeState("UPRIGHT", ((0, 0),))
        s2 = FakeState("HORIZONTAL", ((0, 0), (1, 0)))
        cost = calculate_step_cost(self.game_map, s1, s2, "DOWN")
        self.assertEqual(cost, 1)

    def test_fragile_tiles_cost_formula(self):
        s1 = FakeState("UPRIGHT", ((0, 0),))
        s2 = FakeState("HORIZONTAL", ((0, 1), (0, 2)))
        cost = calculate_step_cost(self.game_map, s1, s2, "RIGHT")
        self.assertEqual(cost, 5)

    def test_heavy_switch_requires_upright_mode(self):
        s1 = FakeState("HORIZONTAL", ((2, 0), (2, 1)))
        s_flat = FakeState("HORIZONTAL", ((2, 1), (2, 2)))
        self.assertEqual(calculate_step_cost(self.game_map, s1, s_flat, "RIGHT"), 1)
        s_upright = FakeState("UPRIGHT", ((2, 2),))
        self.assertEqual(calculate_step_cost(self.game_map, s1, s_upright, "RIGHT"), 2)
>>>>>>> origin/feature/TV5-UCS+A_star_and_cost_calc

    def test_reads_fragile_tiles_from_loaded_game_map_grid(self):
        game_map = parse_map({
            "schema_version": 1, "id": "fragile_map", "name": "Fragile map",
            "difficulty": "easy", "rows": 2, "cols": 4,
            "grid": [
                ["floor", "fragile", "fragile", "floor"],
                ["floor", "floor", "floor", "goal"],
            ],
            "start": [0, 0], "bridges": [], "switches": [],
            "source": {"kind": "original", "reference": "unit test"},
        })
        before = FakeState("UPRIGHT", ((0, 0),))
        after = FakeState("HORIZONTAL", ((0, 1), (0, 2)))
        self.assertEqual(calculate_step_cost(game_map, before, after, "RIGHT"), 5)


class TestTV5UCS(unittest.TestCase):
    """Kiểm thử thuật toán UCS (_search)."""

    def setUp(self):
        self.s, self.a, self.b, self.c, self.g = (
            FakeState("UPRIGHT", ((0, col),)) for col in range(5)
        )

    def search(self, graph, start, goal):
        expanded = []

        def successors(game_map, state):
            self.assertIs(game_map, graph)
            expanded.append(state)
            return game_map.get(fake_key(state), [])

        def is_goal(game_map, state):
            self.assertIs(game_map, graph)
            return goal is not None and fake_key(state) == fake_key(goal)

        result = _search(
            graph, start, state_key=fake_key,
            is_goal=is_goal, successors=successors,
        )
        return result, expanded

    def test_already_solved_returns_empty_immediately(self):
        successors = Mock(side_effect=AssertionError("Goal must not expand"))
        result = _search(
            {}, self.g, state_key=fake_key,
            is_goal=lambda game_map, state: True, successors=successors,
        )
        self.assertEqual(result, ([], 0, 0))
        successors.assert_not_called()

    def test_minimizes_total_cost_over_action_count(self):
        graph = {
            fake_key(self.s): [
                FakeSuccessor("UP", self.a, 5),
                FakeSuccessor("DOWN", self.b, 1),
            ],
            fake_key(self.a): [FakeSuccessor("RIGHT", self.g, 5)],
            fake_key(self.b): [FakeSuccessor("DOWN", self.c, 1)],
            fake_key(self.c): [FakeSuccessor("RIGHT", self.g, 1)],
        }
        result, expanded = self.search(graph, self.s, self.g)
        self.assertEqual(result, (["DOWN", "DOWN", "RIGHT"], 3, 3))
        self.assertEqual(expanded, [self.s, self.b, self.c])

    def test_replaces_path_when_cheaper_route_found_later(self):
        graph = {
            fake_key(self.s): [
                FakeSuccessor("RIGHT", self.a, 10),
                FakeSuccessor("DOWN", self.b, 1),
            ],
            fake_key(self.b): [FakeSuccessor("UP", self.a, 2)],
            fake_key(self.a): [FakeSuccessor("RIGHT", self.g, 1)],
        }
        result, expanded = self.search(graph, self.s, self.g)
        self.assertEqual(result, (["DOWN", "UP", "RIGHT"], 4, 3))
        self.assertEqual(expanded, [self.s, self.b, self.a])

    def test_goal_evaluated_only_on_pop_not_on_push(self):
        graph = {
            fake_key(self.s): [
                FakeSuccessor("FAST_TRAP", self.g, 100),
                FakeSuccessor("RIGHT", self.a, 2),
            ],
            fake_key(self.a): [FakeSuccessor("RIGHT", self.g, 2)],
        }
        result, expanded = self.search(graph, self.s, self.g)
        self.assertEqual(result, (["RIGHT", "RIGHT"], 4, 2))
        self.assertEqual(expanded, [self.s, self.a])

    def test_cycles_and_higher_cost_loops_are_ignored(self):
        graph = {
            fake_key(self.s): [
                FakeSuccessor("RIGHT", self.a, 2),
            ],
            fake_key(self.a): [
                FakeSuccessor("LEFT", self.s, 10),
                FakeSuccessor("DOWN", self.g, 3),
            ],
        }
        result, expanded = self.search(graph, self.s, self.g)
        self.assertEqual(result, (["RIGHT", "DOWN"], 5, 2))
        self.assertEqual(expanded, [self.s, self.a])

    def test_unsolvable_graph_returns_none(self):
        graph = {
            fake_key(self.s): [FakeSuccessor("RIGHT", self.a, 1)],
            fake_key(self.a): [],
        }
        result, expanded = self.search(graph, self.s, self.g)
        self.assertEqual(result, (None, None, 2))
        self.assertEqual(expanded, [self.s, self.a])

    def test_deterministic_and_does_not_mutate_graph(self):
        graph = {
            fake_key(self.s): [FakeSuccessor("RIGHT", self.a, 2)],
            fake_key(self.a): [FakeSuccessor("DOWN", self.g, 2)],
        }
        before = deepcopy((graph, self.s))
        for _ in range(2):
            result, _ = self.search(graph, self.s, self.g)
            self.assertEqual(result, (["RIGHT", "DOWN"], 4, 2))
            self.assertEqual((graph, self.s), before)

    def solve(self, *, start_state=None, timeout_s=60.0, successors=None):
        start_state = self.s if start_state is None else start_state
        return _solve_ucs(
            {}, start_state, map_id="test_map", bridge_ids=(),
            state_key=fake_key,
            is_goal=lambda _game_map, state: state == self.g,
            successors=successors if successors is not None else (lambda *_: []),
            validate_start_state=lambda *_: None,
            timeout_s=timeout_s,
        )

    def test_solve_returns_standard_json_result(self):
        result = self.solve(successors=lambda _map, state: (
            [FakeSuccessor("RIGHT", self.g, 3)] if state == self.s else []
        ))
        payload = json.loads(json.dumps(result.to_dict(), allow_nan=False))
        self.assertEqual(payload["algorithm"], "UCS")
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "SOLVED")
        self.assertEqual(payload["actions"], ["RIGHT"])
        self.assertEqual(payload["metrics"]["solution_cost"], 3)
        self.assertEqual(
            set(payload),
            {
                "schema_version", "map_id", "algorithm", "status", "start_state",
                "actions", "metrics", "timeout_s", "cost_model", "heuristic", "error",
            },
        )

    def test_solve_returns_timeout_with_null_solution_fields(self):
        def slow_successors(*_):
            sleep(0.02)
            return []

        result = self.solve(timeout_s=0.001, successors=slow_successors)
        payload = json.loads(json.dumps(result.to_dict(), allow_nan=False))
        self.assertEqual(payload["status"], "TIMEOUT")
        self.assertIsNone(payload["actions"])
        self.assertIsNone(payload["metrics"]["solution_length"])
        self.assertIsNone(payload["metrics"]["solution_cost"])
        self.assertEqual(payload["metrics"]["expanded_nodes"], 1)

    def test_ucs_uses_engine_successors_and_loaded_game_map_costs(self):
        game_map = parse_map({
            "schema_version": 1, "id": "ucs_fragile", "name": "UCS fragile",
            "difficulty": "easy", "rows": 3, "cols": 6,
            "grid": [
                ["void", "void", "void", "void", "void", "void"],
                ["void", "floor", "fragile", "floor", "goal", "void"],
                ["void", "void", "void", "void", "void", "void"],
            ],
            "start": [1, 1], "bridges": [], "switches": [],
            "source": {"kind": "original", "reference": "unit test"},
        })
        start_state = initial_state(game_map)

        def validate_start(loaded_map, state):
            self.assertIs(loaded_map, game_map)
            self.assertEqual(state, start_state)

        result = _solve_ucs(
            game_map, start_state, map_id=game_map.id, bridge_ids=(),
            state_key=state_key, is_goal=is_goal,
            successors=successors, validate_start_state=validate_start,
        )
        self.assertEqual(result.status, "SOLVED")
        self.assertEqual(result.actions, ["RIGHT", "RIGHT"])
        self.assertEqual(result.metrics.solution_cost, 4)


if __name__ == "__main__":
    unittest.main()