import sys
import unittest
from copy import deepcopy
from dataclasses import dataclass, replace
from unittest.mock import Mock

from src.solvers.dfs.solver import _search


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


class TestTV4DFS(unittest.TestCase):
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

        result = _search(
            graph, start, state_key=fake_key,
            is_goal=lambda game_map, state: goal is not None and fake_key(state) == fake_key(goal),
            successors=successors,
        )
        return result, expanded

    def test_depth_first_path_can_be_longer_and_more_expensive(self):
        graph = {
            fake_key(self.s): [FakeSuccessor("UP", self.a, 3), FakeSuccessor("DOWN", self.b)],
            fake_key(self.a): [FakeSuccessor("RIGHT", self.c)],
            fake_key(self.c): [FakeSuccessor("DOWN", self.g)],
            fake_key(self.b): [FakeSuccessor("RIGHT", self.g)],
        }
        before = deepcopy((graph, self.s))
        for _ in range(2):
            result, expanded = self.search(graph, self.s, self.g)
            self.assertEqual(result, (["UP", "RIGHT", "DOWN"], 5, 3))
            self.assertEqual(expanded, [self.s, self.a, self.c])
            self.assertEqual((graph, self.s), before)

    def test_reverse_push_keeps_engine_action_priority(self):
        for mode, active, actions in (
            ("UPRIGHT", None, ["UP", "DOWN", "LEFT", "RIGHT"]),
            ("SPLIT", 0, ["UP", "DOWN", "LEFT", "RIGHT", "SWITCH"]),
        ):
            with self.subTest(mode=mode):
                start = FakeState(mode, ((1, 1), (3, 3)), active)
                states = [FakeState(mode, ((row, 5), (row, 7)), active) for row in range(5)]
                edges = [FakeSuccessor(action, state) for action, state in zip(actions, states)]
                graph = {fake_key(start): edges}
                result, expanded = self.search(graph, start, None)
                self.assertEqual(result, (None, None, len(actions) + 1))
                self.assertEqual(expanded, [start, *states[:len(actions)]])
                self.assertEqual(graph[fake_key(start)], edges)

    def test_goal_is_checked_on_pop_not_when_generated(self):
        graph = {
            fake_key(self.s): [FakeSuccessor("UP", self.a), FakeSuccessor("RIGHT", self.g)],
            fake_key(self.a): [FakeSuccessor("DOWN", self.c)],
        }
        result, expanded = self.search(graph, self.s, self.g)
        self.assertEqual(result, (["RIGHT"], 1, 3))
        self.assertEqual(expanded, [self.s, self.a, self.c])

    def test_discovery_on_push_preserves_pending_siblings_parent(self):
        graph = {
            fake_key(self.s): [FakeSuccessor("UP", self.a), FakeSuccessor("DOWN", self.b, 3)],
            fake_key(self.a): [FakeSuccessor("RIGHT", self.b)],
            fake_key(self.b): [FakeSuccessor("LEFT", self.g)],
        }
        result, expanded = self.search(graph, self.s, self.g)
        self.assertEqual(result, (["DOWN", "LEFT"], 4, 3))
        self.assertEqual(expanded, [self.s, self.a, self.b])

    def test_cycles_self_loops_and_diamond_expand_each_full_key_once(self):
        graph = {
            fake_key(self.s): [FakeSuccessor("UP", self.a), FakeSuccessor("DOWN", self.b)],
            fake_key(self.a): [FakeSuccessor("LEFT", self.s), FakeSuccessor("RIGHT", self.c)],
            fake_key(self.b): [FakeSuccessor("RIGHT", replace(self.c))],
            fake_key(self.c): [FakeSuccessor("UP", self.a), FakeSuccessor("DOWN", self.c)],
        }
        result, expanded = self.search(graph, self.s, None)
        self.assertEqual(result, (None, None, 4))
        self.assertEqual(expanded, [self.s, self.a, self.c, self.b])

    def test_same_cells_with_different_mode_bridges_or_active_are_distinct(self):
        pairs = (
            (self.a, replace(self.a, mode="HORIZONTAL")),
            (replace(self.a, bridges=(False,)), replace(self.a, bridges=(True,))),
            (replace(self.a, mode="SPLIT", active=0), replace(self.a, mode="SPLIT", active=1)),
        )
        for first, second in pairs:
            with self.subTest(first=first, second=second):
                graph = {
                    fake_key(self.s): [FakeSuccessor("UP", first)],
                    fake_key(first): [FakeSuccessor("SWITCH", second)],
                    fake_key(second): [FakeSuccessor("RIGHT", self.g)],
                }
                result, _ = self.search(graph, self.s, self.g)
                self.assertEqual(result, (["UP", "SWITCH", "RIGHT"], 3, 3))

    def test_non_goal_without_successors_exhausts_stack(self):
        result, expanded = self.search({}, self.s, self.g)
        self.assertEqual(result, (None, None, 1))
        self.assertEqual(expanded, [self.s])

    def test_already_solved_skips_keys_successors_and_runtime(self):
        key, successors, runtime = Mock(), Mock(), Mock()
        result = _search({}, self.g, state_key=key, is_goal=lambda *_: True,
                         successors=successors, runtime=runtime)
        self.assertEqual(result, ([], 0, 0))
        key.assert_not_called()
        successors.assert_not_called()
        self.assertEqual(runtime.mock_calls, [])

    def test_chain_beyond_recursion_limit(self):
        limit = sys.getrecursionlimit()
        states = [FakeState("UPRIGHT", ((0, col),)) for col in range(limit + 20)]
        graph = {
            fake_key(state): [FakeSuccessor("RIGHT", next_state)]
            for state, next_state in zip(states, states[1:])
        }
        result, expanded = self.search(graph, states[0], states[-1])
        self.assertEqual(result, (["RIGHT"] * (len(states) - 1), len(states) - 1, len(states) - 1))
        self.assertEqual(expanded, states[:-1])
        self.assertEqual(sys.getrecursionlimit(), limit)

    def test_direct_core_propagates_callback_errors(self):
        for name in ("state_key", "is_goal", "successors"):
            with self.subTest(callback=name):
                callbacks = dict(state_key=fake_key, is_goal=lambda *_: False, successors=lambda *_: [])
                callbacks[name] = Mock(side_effect=ValueError("callback failed"))
                with self.assertRaisesRegex(ValueError, "callback failed"):
                    _search({}, self.s, **callbacks)


if __name__ == "__main__":
    unittest.main()
