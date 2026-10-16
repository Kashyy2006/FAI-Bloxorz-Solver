"""Tests for basic rules that unblock GUI and solver integration."""

import unittest
from pathlib import Path

from src.engine import (
    Action, Mode, State, Status, initial_state, is_goal, load_map, parse_map,
    state_key, step_cost, successors, transition,
)


def make_map(*, fragile=(), goal=(6, 6), start=(3, 3)):
    rows = [["floor" for _ in range(8)] for _ in range(8)]
    for row in range(8):
        for col in range(8):
            if row in (0, 7) or col in (0, 7):
                rows[row][col] = "void"
    rows[goal[0]][goal[1]] = "goal"
    for row, col in fragile:
        rows[row][col] = "fragile"
    rows[start[0]][start[1]] = "floor"
    return parse_map({
        "schema_version": 1, "id": "test_map", "name": "Engine test map",
        "difficulty": "easy", "rows": 8, "cols": 8, "grid": rows,
        "start": list(start), "bridges": [], "switches": [],
        "source": {"kind": "original", "reference": "unit test"},
    })


class StateTests(unittest.TestCase):
    def test_state_canonicalizes_cells_and_key(self):
        first = State(Mode.HORIZONTAL, ((2, 4), (2, 3)))
        second = State(Mode.HORIZONTAL, ((2, 3), (2, 4)))
        self.assertEqual(first.cells, ((2, 3), (2, 4)))
        self.assertEqual(state_key(first), state_key(second))

    def test_invalid_orientation_geometry_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "adjacent in one row"):
            State(Mode.HORIZONTAL, ((1, 1), (2, 1)))


class BasicTransitionTests(unittest.TestCase):
    def setUp(self):
        self.game_map = make_map()

    def test_all_twelve_block_roll_transitions(self):
        cases = [
            (Mode.UPRIGHT, ((3, 3),), Action.UP, Mode.VERTICAL, ((1, 3), (2, 3))),
            (Mode.UPRIGHT, ((3, 3),), Action.DOWN, Mode.VERTICAL, ((4, 3), (5, 3))),
            (Mode.UPRIGHT, ((3, 3),), Action.LEFT, Mode.HORIZONTAL, ((3, 1), (3, 2))),
            (Mode.UPRIGHT, ((3, 3),), Action.RIGHT, Mode.HORIZONTAL, ((3, 4), (3, 5))),
            (Mode.HORIZONTAL, ((3, 3), (3, 4)), Action.UP, Mode.HORIZONTAL, ((2, 3), (2, 4))),
            (Mode.HORIZONTAL, ((3, 3), (3, 4)), Action.DOWN, Mode.HORIZONTAL, ((4, 3), (4, 4))),
            (Mode.HORIZONTAL, ((3, 3), (3, 4)), Action.LEFT, Mode.UPRIGHT, ((3, 2),)),
            (Mode.HORIZONTAL, ((3, 3), (3, 4)), Action.RIGHT, Mode.UPRIGHT, ((3, 5),)),
            (Mode.VERTICAL, ((3, 3), (4, 3)), Action.UP, Mode.UPRIGHT, ((2, 3),)),
            (Mode.VERTICAL, ((3, 3), (4, 3)), Action.DOWN, Mode.UPRIGHT, ((5, 3),)),
            (Mode.VERTICAL, ((3, 3), (4, 3)), Action.LEFT, Mode.VERTICAL, ((3, 2), (4, 2))),
            (Mode.VERTICAL, ((3, 3), (4, 3)), Action.RIGHT, Mode.VERTICAL, ((3, 4), (4, 4))),
        ]
        for mode, cells, action, expected_mode, expected_cells in cases:
            with self.subTest(mode=mode, action=action):
                result = transition(self.game_map, State(mode, cells), action)
                self.assertEqual(result.status, Status.OK)
                self.assertEqual(result.next_state.mode, expected_mode)
                self.assertEqual(result.next_state.cells, expected_cells)

    def test_falling_outside_map_and_over_void_loses(self):
        self.assertEqual(transition(self.game_map, State(Mode.UPRIGHT, ((1, 1),)),
                                    Action.UP).reason, "OUT_OF_BOUNDS")
        self.assertEqual(transition(self.game_map, State(Mode.UPRIGHT, ((2, 3),)),
                                    Action.UP).reason, "VOID")

    def test_goal_requires_upright_and_terminal_state_rejects_moves(self):
        goal_state = State(Mode.UPRIGHT, (self.game_map.goal,))
        self.assertTrue(is_goal(self.game_map, goal_state))
        self.assertEqual(transition(self.game_map, goal_state, Action.LEFT).reason,
                         "ALREADY_WON")
        self.assertFalse(is_goal(self.game_map,
                                 State(Mode.HORIZONTAL, ((6, 5), (6, 6)))))

    def test_fragile_support_and_upright_loss(self):
        game_map = make_map(fragile=((3, 5),))
        result = transition(game_map, State(Mode.UPRIGHT, ((3, 3),)), Action.RIGHT)
        self.assertEqual(result.status, Status.OK)
        result = transition(game_map, State(Mode.HORIZONTAL, ((3, 3), (3, 4))),
                            Action.RIGHT)
        self.assertEqual((result.status, result.reason),
                         (Status.LOST, "FRAGILE_UPRIGHT"))

    def test_fragile_cost_counts_newly_occupied_cells(self):
        game_map = make_map(fragile=((3, 5),))
        before = State(Mode.UPRIGHT, ((3, 3),))
        after = transition(game_map, before, Action.RIGHT).next_state
        self.assertEqual(step_cost(game_map, before, Action.RIGHT, after), 3)

    def test_successors_are_ordered_and_omit_losing_moves(self):
        result = successors(self.game_map, initial_state(self.game_map))
        self.assertEqual([item.action for item in result],
                         [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT])
        self.assertTrue(all(item.cost == 1 for item in result))


class MapValidationTests(unittest.TestCase):
    def test_load_example_map(self):
        path = Path(__file__).parents[2] / "data" / "maps" / "basic_01.json"
        self.assertEqual(load_map(path).id, "basic_01")

    def test_ragged_grid_error_has_location(self):
        data = {"schema_version": 1, "id": "bad", "name": "Bad grid",
                "difficulty": "easy", "rows": 2, "cols": 2,
                "grid": [["floor", "goal"], ["floor"]], "start": [0, 0],
                "bridges": [], "switches": [],
                "source": {"kind": "original", "reference": "test"}}
        with self.assertRaisesRegex(ValueError, r"grid\[1\]"):
            parse_map(data)

    def test_boolean_is_not_integer_coordinate(self):
        data = {"schema_version": 1, "id": "bad", "name": "Bad start",
                "difficulty": "easy", "rows": 1, "cols": 2,
                "grid": [["floor", "goal"]], "start": [False, 0],
                "bridges": [], "switches": [],
                "source": {"kind": "original", "reference": "test"}}
        with self.assertRaisesRegex(ValueError, "integer coordinates"):
            parse_map(data)

    def test_advanced_tiles_are_rejected_at_basic_milestone(self):
        data = {"schema_version": 1, "id": "advanced", "name": "Future map",
                "difficulty": "easy", "rows": 1, "cols": 2,
                "grid": [["soft", "goal"]], "start": [0, 0],
                "bridges": [], "switches": [],
                "source": {"kind": "original", "reference": "test"}}
        with self.assertRaisesRegex(ValueError, "advanced tiles"):
            parse_map(data)


if __name__ == "__main__":
    unittest.main()

