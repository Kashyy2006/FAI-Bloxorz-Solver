import unittest
from dataclasses import dataclass
from unittest.mock import patch

from src.engine import Mode, State, parse_map, state_key, successors, is_goal
from src.engine.map_loader import GameMap
from src.solvers.astar.solver import _search
from src.solvers.costs.calc import (
    calculate_heuristic,
    heuristic_name,
    manhattan_orientation,
    prepare_heuristic,
    reverse_bfs_heuristic,
)
from src.contracts import GOAL_INDICATOR, MANHATTAN


def line_map():
    return parse_map({
        "schema_version": 1,
        "id": "astar_line",
        "name": "A* line",
        "difficulty": "easy",
        "rows": 1,
        "cols": 4,
        "grid": [["floor", "floor", "floor", "goal"]],
        "start": [0, 0],
        "bridges": [],
        "switches": [],
        "source": {"kind": "original", "reference": "unit test"},
    })


class HeuristicTest(unittest.TestCase):
    def test_reverse_bfs_returns_goal_distance_for_orientation_states(self):
        game_map = line_map()
        start = State(Mode.UPRIGHT, ((0, 0),))
        horizontal = State(Mode.HORIZONTAL, ((0, 1), (0, 2)))
        goal = State(Mode.UPRIGHT, (game_map.goal,))

        self.assertEqual(reverse_bfs_heuristic(game_map, start), 2)
        self.assertEqual(reverse_bfs_heuristic(game_map, horizontal), 1)
        self.assertEqual(reverse_bfs_heuristic(game_map, goal), 0)

    def test_manhattan_heuristic_accounts_for_orientation(self):
        game_map = GameMap(
            "orientation",
            "Orientation",
            "easy",
            3,
            5,
            (
                ("floor", "floor", "floor", "goal", "floor"),
                ("floor", "floor", "floor", "floor", "floor"),
                ("floor", "floor", "floor", "floor", "floor"),
            ),
            (1, 1),
            (0, 3),
        )
        upright = State(Mode.UPRIGHT, ((0, 0),))
        horizontal = State(Mode.HORIZONTAL, ((0, 0), (0, 1)))
        vertical = State(Mode.VERTICAL, ((0, 0), (1, 0)))

        # A roll can move the occupied footprint by up to two cells.
        self.assertEqual(manhattan_orientation(game_map, upright), 2)
        self.assertEqual(manhattan_orientation(game_map, horizontal), 1)
        self.assertEqual(manhattan_orientation(game_map, vertical), 2)
        from src.solvers.solve import solve
        for state in (upright, horizontal, vertical):
            optimal = solve(game_map, state, "UCS")
            self.assertEqual(optimal["status"], "SOLVED")
            self.assertLessEqual(manhattan_orientation(game_map, state),
                                 optimal["metrics"]["solution_cost"])

    def test_bridge_and_split_maps_skip_static_reverse_graph(self):
        from pathlib import Path
        from src.engine import load_map, initial_state
        root = Path(__file__).resolve().parents[2]
        for name, strategy, expected in (
            ("advanced_bridge_01.json", MANHATTAN, 5),
            ("advanced_split_01.json", GOAL_INDICATOR, 1),
        ):
            game_map = load_map(root / "data/maps" / name)
            state = initial_state(game_map)
            with patch("src.solvers.costs.calc._reverse_bfs_distances",
                       side_effect=AssertionError("cached static graph must not run")), \
                 patch("src.solvers.costs.calc._build_reverse_bfs_distances",
                       side_effect=AssertionError("static graph must not be built")):
                self.assertEqual(heuristic_name(game_map), strategy)
                self.assertEqual(calculate_heuristic(game_map, state), expected)
                self.assertEqual(reverse_bfs_heuristic(game_map, state), expected)
                self.assertEqual(manhattan_orientation(game_map, state), expected)
                self.assertEqual(prepare_heuristic(game_map, state)(state), expected)
                goal = State(Mode.UPRIGHT, (game_map.goal,), bridges=state.bridges)
                self.assertEqual(calculate_heuristic(game_map, goal), 0)
                for step in successors(game_map, state):
                    self.assertLessEqual(calculate_heuristic(game_map, state),
                                         step.cost + calculate_heuristic(game_map, step.state))

    def test_manhattan_lying_on_goal_uses_consistent_one_step_bound(self):
        grid = [["floor"] * 8 for _ in range(8)]
        grid[4][4] = "goal"
        game_map = GameMap("goal_bound", "Goal bound", "easy", 8, 8,
                           tuple(tuple(row) for row in grid), (0, 0), (4, 4))
        for state in (State(Mode.HORIZONTAL, ((4, 4), (4, 5))),
                      State(Mode.VERTICAL, ((4, 4), (5, 4)))):
            self.assertEqual(manhattan_orientation(game_map, state), 1)
            for edge in successors(game_map, state):
                self.assertLessEqual(manhattan_orientation(game_map, state),
                                     edge.cost + manhattan_orientation(game_map, edge.state))
        self.assertEqual(manhattan_orientation(game_map, State(Mode.UPRIGHT, ((4, 4),))), 0)

    def test_manhattan_is_consistent_on_all_open_board_rolls(self):
        grid = [["floor"] * 5 for _ in range(5)]
        grid[2][2] = "goal"
        game_map = GameMap("consistency", "Consistency", "easy", 5, 5,
                           tuple(tuple(row) for row in grid), (0, 0), (2, 2))
        for row in range(5):
            for col in range(5):
                states = [State(Mode.UPRIGHT, ((row, col),))]
                if col < 4:
                    states.append(State(Mode.HORIZONTAL, ((row, col), (row, col + 1))))
                if row < 4:
                    states.append(State(Mode.VERTICAL, ((row, col), (row + 1, col))))
                for state in states:
                    for edge in successors(game_map, state):
                        self.assertLessEqual(manhattan_orientation(game_map, state),
                                             edge.cost + manhattan_orientation(game_map, edge.state))

    def test_auto_heuristic_uses_reverse_bfs_on_small_map(self):
        game_map = line_map()
        state = State(Mode.UPRIGHT, ((0, 0),))
        with patch(
            "src.solvers.costs.calc.reverse_bfs_heuristic", return_value=7
        ) as reverse, patch(
            "src.solvers.costs.calc.manhattan_orientation", return_value=3
        ) as manhattan:
            self.assertEqual(calculate_heuristic(game_map, state), 7)
        reverse.assert_called_once_with(game_map, state)
        manhattan.assert_not_called()

    def test_auto_heuristic_uses_manhattan_on_large_map(self):
        size = 30
        game_map = GameMap(
            "large",
            "Large",
            "hard",
            size,
            size,
            tuple(tuple("floor" for _ in range(size)) for _ in range(size - 1))
            + (tuple(["floor"] * (size - 1) + ["goal"]),),
            (0, 0),
            (size - 1, size - 1),
        )
        state = State(Mode.UPRIGHT, ((0, 0),))
        with patch(
            "src.solvers.costs.calc.reverse_bfs_heuristic"
        ) as reverse, patch(
            "src.solvers.costs.calc.manhattan_orientation", return_value=11
        ) as manhattan:
            self.assertEqual(calculate_heuristic(game_map, state), 11)
        reverse.assert_not_called()
        manhattan.assert_called_once_with(game_map, state)


@dataclass(frozen=True)
class FakeState:
    name: str


@dataclass(frozen=True)
class FakeSuccessor:
    action: str
    state: FakeState
    cost: int


class AStarSearchTest(unittest.TestCase):
    def test_search_uses_automatic_heuristic_and_minimizes_total_cost(self):
        start, direct, detour, goal = (
            FakeState(name) for name in ("start", "direct", "detour", "goal")
        )
        graph = {
            "start": [
                FakeSuccessor("EXPENSIVE", direct, 8),
                FakeSuccessor("STEP", detour, 1),
            ],
            "direct": [FakeSuccessor("FINISH", goal, 1)],
            "detour": [FakeSuccessor("STEP", direct, 1)],
        }
        with patch(
            "src.solvers.astar.solver.calculate_heuristic", return_value=0
        ) as heuristic:
            result = _search(
                object(),
                start,
                state_key=lambda state: state.name,
                is_goal=lambda *args: args[1] == goal,
                successors=lambda *args: graph.get(args[1].name, []),
            )

        self.assertEqual(result, (["STEP", "STEP", "FINISH"], 3, 3))
        self.assertEqual(heuristic.call_count, 5)

    def test_engine_search_solves_basic_map(self):
        game_map = line_map()
        start = State(Mode.UPRIGHT, (game_map.start,))

        result = _search(
            game_map,
            start,
            state_key=state_key,
            is_goal=is_goal,
            successors=successors,
        )

        self.assertEqual(result, (["RIGHT", "RIGHT"], 2, 2))
