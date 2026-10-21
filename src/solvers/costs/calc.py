from src.contracts import GOAL_INDICATOR, REVERSE_BFS, MANHATTAN
from collections import deque
from functools import lru_cache

from src.engine.models import Mode, State
from src.engine.rules import state_key, successors


def calculate_step_cost(game_map, current_state, next_state, action: str) -> int:
    """Canonical cost: new final cells contribute fragile +2, soft/heavy +1.

    Heavy contributes only for an upright destination; SWITCH always costs 1.
    This is a cost convention, independent of transition activation events.
    """
    if action == "SWITCH":
        return 1

    new_cells = set(next_state.cells) - set(current_state.cells)
    fragile_count = 0
    triggered_switches = 0
    for cell in new_cells:
        tile = game_map.tile_at(cell)
        fragile_count += tile == "fragile"
        triggered_switches += (
            tile == "soft"
            or (tile == "heavy" and next_state.mode in (Mode.UPRIGHT, "UPRIGHT"))
        )
    return 1 + 2 * fragile_count + triggered_switches


_REVERSE_BFS_STATE_LIMIT = 1000


def _needs_dynamic_heuristic(game_map, state):
    return bool(game_map.bridges or game_map.switches or state.mode == Mode.SPLIT)


def _goal_indicator(game_map, state):
    return 0 if state.mode == Mode.UPRIGHT and state.cells == (game_map.goal,) else 1


def _build_reverse_bfs_distances(game_map, check_stop=lambda: None) -> dict[tuple, int]:
    """Shortest action-count distances to the goal for every basic map state."""
    states = []
    for row in range(game_map.rows):
        check_stop()
        for col in range(game_map.cols):
            check_stop()
            cell = (row, col)
            tile = game_map.tile_at(cell)
            if tile not in ("void", "fragile"):
                states.append(State(Mode.UPRIGHT, (cell,)))
            if tile == "void":
                continue
            if col + 1 < game_map.cols and game_map.tile_at((row, col + 1)) != "void":
                states.append(State(Mode.HORIZONTAL, (cell, (row, col + 1))))
            if row + 1 < game_map.rows and game_map.tile_at((row + 1, col)) != "void":
                states.append(State(Mode.VERTICAL, (cell, (row + 1, col))))

    predecessors: dict[tuple, list[tuple]] = {}
    for state in states:
        check_stop()
        source_key = state_key(state)
        for successor in successors(game_map, state):
            check_stop()
            target_key = state_key(successor.state)
            predecessors.setdefault(target_key, []).append(source_key)

    goal = State(Mode.UPRIGHT, (game_map.goal,))
    goal_key = state_key(goal)
    distances = {goal_key: 0}
    frontier = deque([goal_key])
    while frontier:
        check_stop()
        target_key = frontier.popleft()
        next_distance = distances[target_key] + 1
        for source_key in predecessors.get(target_key, ()):
            check_stop()
            if source_key not in distances:
                distances[source_key] = next_distance
                frontier.append(source_key)
    check_stop()
    return distances


@lru_cache(maxsize=32)
def _reverse_bfs_distances(game_map):
    """Convenience cache for standalone heuristic inspection, never benchmark search."""
    return _build_reverse_bfs_distances(game_map)


def prepare_heuristic(game_map, state, check_stop=lambda: None):
    """Build a per-search evaluator under the caller's timer/memory/cancel guards."""
    check_stop()
    strategy = heuristic_name(game_map, state.mode == Mode.SPLIT)
    if strategy == GOAL_INDICATOR:
        return lambda current: _goal_indicator(game_map, current)
    if strategy == MANHATTAN:
        return lambda current: manhattan_orientation(game_map, current)
    distances = _build_reverse_bfs_distances(game_map, check_stop)
    def estimate(current):
        check_stop()
        distance = distances.get(state_key(current))
        return manhattan_orientation(game_map, current) if distance is None else distance
    return estimate


def reverse_bfs_heuristic(game_map, state) -> int:
    """Estimate remaining actions using distances from a reverse goal BFS."""
    if _needs_dynamic_heuristic(game_map, state):
        return _goal_indicator(game_map, state)
    distances = _reverse_bfs_distances(game_map)
    key = state_key(state)
    if key in distances:
        return distances[key]
    # Unreachable static poses have no reverse distance; use the Manhattan lower bound.
    return manhattan_orientation(game_map, state)

def manhattan_orientation(game_map, state) -> int:
    """Admissible orientation-aware Manhattan lower bound on remaining actions."""
    if _needs_dynamic_heuristic(game_map, state):
        return _goal_indicator(game_map, state)
    goal_row, goal_col = game_map.goal
    min_dist = min(abs(row - goal_row) + abs(col - goal_col) for row, col in state.cells)
    base_steps = (min_dist + 1) // 2
    if state.mode is not Mode.UPRIGHT and min_dist == 0:
        return max(4, base_steps)
    return base_steps


@lru_cache(maxsize=64)
def heuristic_name(game_map, split=False) -> str:
    """Automatically choose the stronger practical heuristic for this map."""
    # The static reverse graph omits bridge flags and split-cube states.
    # A goal indicator remains admissible/consistent with teleport and cost >= 1.
    if game_map.bridges or game_map.switches or split:
        return GOAL_INDICATOR
    state_count = 0
    for row in range(game_map.rows):
        for col in range(game_map.cols):
            cell = (row, col)
            tile = game_map.tile_at(cell)
            state_count += tile not in ("void", "fragile")
            if tile != "void":
                state_count += (
                    col + 1 < game_map.cols
                    and game_map.tile_at((row, col + 1)) != "void"
                )
                state_count += (
                    row + 1 < game_map.rows
                    and game_map.tile_at((row + 1, col)) != "void"
                )

    return REVERSE_BFS if state_count <= _REVERSE_BFS_STATE_LIMIT else MANHATTAN


def calculate_heuristic(game_map, state) -> int:
    strategy = heuristic_name(game_map, state.mode == Mode.SPLIT)
    if strategy == GOAL_INDICATOR:
        return _goal_indicator(game_map, state)
    if strategy == REVERSE_BFS:
        return reverse_bfs_heuristic(game_map, state)
    return manhattan_orientation(game_map, state)
