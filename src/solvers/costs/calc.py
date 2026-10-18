from collections import deque
from functools import lru_cache

from src.engine.models import Mode, State
from src.engine.rules import state_key, successors


def calculate_step_cost(game_map, current_state, next_state, action: str) -> int:
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


@lru_cache(maxsize=32)
def _reverse_bfs_distances(game_map) -> dict[tuple, int]:
    """Shortest action-count distances to the goal for every basic map state."""
    states = []
    for row in range(game_map.rows):
        for col in range(game_map.cols):
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
        source_key = state_key(state)
        for successor in successors(game_map, state):
            target_key = state_key(successor.state)
            predecessors.setdefault(target_key, []).append(source_key)

    goal = State(Mode.UPRIGHT, (game_map.goal,))
    goal_key = state_key(goal)
    distances = {goal_key: 0}
    frontier = deque([goal_key])
    while frontier:
        target_key = frontier.popleft()
        next_distance = distances[target_key] + 1
        for source_key in predecessors.get(target_key, ()):
            if source_key not in distances:
                distances[source_key] = next_distance
                frontier.append(source_key)
    return distances


def reverse_bfs_heuristic(game_map, state) -> int:
    """Estimate remaining actions using distances from a reverse goal BFS."""
    distances = _reverse_bfs_distances(game_map)
    key = state_key(state)
    if key in distances:
        return distances[key]
    # Nếu gặp cầu chưa mở, sử dụng manhattan làm fallback.
    return manhattan_orientation(game_map, state)

def manhattan_orientation(game_map, state) -> int:
    """Admissible orientation-aware Manhattan lower bound on remaining actions."""
    goal_row, goal_col = game_map.goal
    min_dist = min(abs(row - goal_row) + abs(col - goal_col) for row, col in state.cells)
    base_steps = (min_dist + 1) // 2
    if state.mode is not Mode.UPRIGHT and min_dist == 0:
        return max(4, base_steps)
    return base_steps


def calculate_heuristic(game_map, state) -> int:
    """Automatically choose the stronger practical heuristic for this map."""
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

    if state_count <= _REVERSE_BFS_STATE_LIMIT:
        return reverse_bfs_heuristic(game_map, state)
    return manhattan_orientation(game_map, state)
