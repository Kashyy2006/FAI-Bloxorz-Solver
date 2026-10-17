import unittest
from copy import deepcopy
from dataclasses import dataclass
from unittest.mock import Mock
from src.solvers.ucs.solver import _search
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



def fake_key(state):
    return (state.mode, state.cells, state.active, state.bridges)


class TestTV5CostCalculation(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()