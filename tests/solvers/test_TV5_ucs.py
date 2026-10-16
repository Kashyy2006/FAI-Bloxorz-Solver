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


@dataclass(frozen=True)
class FakeMap:
    fragile_tiles: set = frozenset()
    soft_switches: set = frozenset()
    heavy_switches: set = frozenset()


def fake_key(state):
    return (state.mode, state.cells, state.active, state.bridges)


class TestTV5CostCalculation(unittest.TestCase):
    """Kiểm thử riêng cho hàm tính chi phí bước đi (calculate_step_cost)."""

    def setUp(self):
        self.game_map = FakeMap(
            fragile_tiles={(0, 1), (0, 2)},
            soft_switches={(1, 1)},
            heavy_switches={(2, 2)},
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