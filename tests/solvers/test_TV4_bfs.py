import unittest
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, replace
from unittest.mock import Mock, patch

from src.solvers.bfs.solver import _search


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


class TestTV4BFS(unittest.TestCase):
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

    def test_shortest_path_checks_goal_on_dequeue_without_expanding_it(self):
        graph = {
            fake_key(self.s): [
                FakeSuccessor("UP", self.a), FakeSuccessor("RIGHT", self.g),
            ],
            fake_key(self.a): [FakeSuccessor("DOWN", self.b)],
        }
        result, expanded = self.search(graph, self.s, self.g)
        self.assertEqual(result, (["RIGHT"], 1, 2))
        self.assertEqual(expanded, [self.s, self.a])

    def test_equal_depth_paths_keep_first_parent_and_its_cost(self):
        for first_cost in (1, 3):
            with self.subTest(first_cost=first_cost):
                graph = {
                    fake_key(self.s): [
                        FakeSuccessor("UP", self.a, first_cost),
                        FakeSuccessor("DOWN", self.b),
                    ],
                    fake_key(self.a): [
                        FakeSuccessor("RIGHT", self.g, first_cost),
                    ],
                    fake_key(self.b): [FakeSuccessor("LEFT", self.g)],
                }
                result, expanded = self.search(graph, self.s, self.g)
                self.assertEqual(result, (["UP", "RIGHT"], 2 * first_cost, 3))
                self.assertEqual(expanded, [self.s, self.a, self.b])

    def test_minimizes_actions_rather_than_total_cost(self):
        graph = {
            fake_key(self.s): [
                FakeSuccessor("UP", self.a, 3), FakeSuccessor("DOWN", self.b),
            ],
            fake_key(self.a): [FakeSuccessor("RIGHT", self.g, 3)],
            fake_key(self.b): [FakeSuccessor("DOWN", self.c)],
            fake_key(self.c): [FakeSuccessor("RIGHT", self.g)],
        }
        result, expanded = self.search(graph, self.s, self.g)
        self.assertEqual(result, (["UP", "RIGHT"], 6, 3))
        self.assertEqual(expanded, [self.s, self.a, self.b])

    def test_diamond_cycles_and_self_loop_enqueue_each_key_once(self):
        graph = {
            fake_key(self.s): [
                FakeSuccessor("UP", self.a), FakeSuccessor("DOWN", self.b),
            ],
            fake_key(self.a): [
                FakeSuccessor("DOWN", self.s), FakeSuccessor("RIGHT", self.c),
            ],
            fake_key(self.b): [
                FakeSuccessor("UP", self.s),
                FakeSuccessor("RIGHT", replace(self.c)),
            ],
            fake_key(self.c): [
                FakeSuccessor("LEFT", self.a), FakeSuccessor("RIGHT", self.c),
            ],
        }
        enqueued = []

        class RecordingDeque(deque):
            def __init__(self, items=()):
                super().__init__(items)
                enqueued.extend(self)

            def append(self, item):
                enqueued.append(item)
                super().append(item)

        with patch("src.solvers.bfs.solver.deque", RecordingDeque):
            result, expanded = self.search(graph, self.s, None)

        self.assertEqual(result, (None, None, 4))
        self.assertEqual(expanded, [self.s, self.a, self.b, self.c])
        self.assertEqual(
            [fake_key(state) for state, _ in enqueued],
            [fake_key(state) for state in (self.s, self.a, self.b, self.c)],
        )

    def test_non_goal_without_successors_is_unsolvable(self):
        result, expanded = self.search({}, self.s, self.g)
        self.assertEqual(result, (None, None, 1))
        self.assertEqual(expanded, [self.s])

    def test_already_solved_does_not_initialize_search_or_expand(self):
        successors = Mock(side_effect=AssertionError("Goal must not expand"))
        state_key = Mock(side_effect=AssertionError("Search must not start"))
        with patch("src.solvers.bfs.solver.deque") as queue:
            result = _search(
                {}, self.g, state_key=state_key,
                is_goal=lambda game_map, state: True, successors=successors,
            )
        self.assertEqual(result, ([], 0, 0))
        queue.assert_not_called()
        state_key.assert_not_called()
        successors.assert_not_called()

    def test_same_cells_with_different_bridges_remain_distinct(self):
        closed = replace(self.a, bridges=(False,))
        opened = replace(closed, bridges=(True,))
        graph = {
            fake_key(self.s): [
                FakeSuccessor("UP", closed), FakeSuccessor("DOWN", opened),
            ],
            fake_key(opened): [FakeSuccessor("RIGHT", self.g)],
        }
        result, expanded = self.search(graph, self.s, self.g)
        self.assertEqual(result, (["DOWN", "RIGHT"], 2, 3))
        self.assertEqual(expanded, [self.s, closed, opened])

    def test_switch_changes_active_and_counts_as_an_action(self):
        first = FakeState("SPLIT", ((1, 1), (3, 3)), 0, (False,))
        second = replace(first, active=1)
        graph = {
            fake_key(first): [FakeSuccessor("SWITCH", second)],
            fake_key(second): [
                FakeSuccessor("RIGHT", self.g), FakeSuccessor("SWITCH", first),
            ],
        }
        result, expanded = self.search(graph, first, self.g)
        self.assertEqual(result, (["SWITCH", "RIGHT"], 2, 2))
        self.assertEqual(expanded, [first, second])

    def test_uses_engine_key_for_all_modes(self):
        states = [
            self.s,
            FakeState("HORIZONTAL", ((0, 1), (0, 2))),
            FakeState("VERTICAL", ((1, 2), (2, 2))),
            FakeState("SPLIT", ((1, 3), (3, 3)), 0),
            self.g,
        ]
        actions = ["RIGHT", "DOWN", "RIGHT", "UP"]
        graph = {
            fake_key(state): [FakeSuccessor(action, next_state)]
            for state, action, next_state in zip(states, actions, states[1:])
        }
        key = Mock(side_effect=lambda state: ("engine", fake_key(state)))
        result = _search(
            graph, states[0], state_key=key,
            is_goal=lambda game_map, state: fake_key(state) == fake_key(self.g),
            successors=lambda game_map, state: game_map.get(fake_key(state), []),
        )
        self.assertEqual(result, (actions, 4, 4))
        self.assertEqual({call.args[0] for call in key.call_args_list}, set(states))
        for state in states:
            self.assertEqual(fake_key(state), (
                state.mode, state.cells, state.active, state.bridges,
            ))

    def test_inputs_unchanged_and_repeated_runs_are_deterministic(self):
        graph = {
            fake_key(self.s): [FakeSuccessor("RIGHT", self.a)],
            fake_key(self.a): [FakeSuccessor("DOWN", self.g)],
        }
        before = deepcopy((graph, self.s))
        for goal, expected in (
            (self.g, (["RIGHT", "DOWN"], 2, 2)),
            (None, (None, None, 3)),
        ):
            with self.subTest(goal=goal):
                for _ in range(2):
                    result, _ = self.search(graph, self.s, goal)
                    self.assertEqual(result, expected)
                    self.assertEqual((graph, self.s), before)

    def test_callback_errors_propagate_instead_of_becoming_unsolvable(self):
        for failing_callback in ("state_key", "is_goal", "successors"):
            with self.subTest(callback=failing_callback):
                callbacks = {
                    "state_key": fake_key,
                    "is_goal": lambda game_map, state: False,
                    "successors": lambda game_map, state: [],
                }
                callbacks[failing_callback] = Mock(
                    side_effect=RuntimeError("Engine failed"),
                )
                with self.assertRaisesRegex(RuntimeError, "Engine failed"):
                    _search({}, self.s, **callbacks)


if __name__ == "__main__":
    unittest.main()
