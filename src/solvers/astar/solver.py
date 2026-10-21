<<<<<<< HEAD
"""A* with a teleport-safe goal-indicator heuristic."""
from src.solvers.ucs.solver import _search as weighted_search


def _search(game_map, start_state, *, state_key, is_goal, successors, runtime=None):
    return weighted_search(game_map, start_state, state_key=state_key,
                           is_goal=is_goal, successors=successors, runtime=runtime,
                           heuristic=lambda m, s: 0 if is_goal(m, s) else 1)
=======
import heapq
from itertools import count

from src.solvers.common.path import reconstruct_actions
from src.solvers.costs.calc import calculate_heuristic


def _search(game_map, start_state, *, state_key, is_goal, successors, runtime=None):
    """Run A* while letting the map-aware dispatcher choose h(state)."""
    if is_goal(game_map, start_state):
        return [], 0, 0

    if runtime is not None:
        runtime.start()
    check_stop = runtime.check_stop if runtime is not None else lambda: None
    check_stop()

    start_key = state_key(start_state)
    counter = count()
    frontier = [
        (calculate_heuristic(game_map, start_state), 0, next(counter), start_state)
    ]
    best_cost = {start_key: 0}
    parent = {start_key: None}
    action_to = {}
    expanded_nodes = 0

    while frontier:
        check_stop()
        _, cost, _, state = heapq.heappop(frontier)
        key = state_key(state)
        if cost != best_cost.get(key):
            continue
        if is_goal(game_map, state):
            if runtime is not None:
                runtime.mark_search_stopped()
            return reconstruct_actions(parent, action_to, key), cost, expanded_nodes

        expanded_nodes += 1
        if runtime is not None:
            runtime.metrics.expanded_nodes = expanded_nodes
        for successor in successors(game_map, state):
            check_stop()
            next_state = successor.state
            next_key = state_key(next_state)
            new_cost = cost + successor.cost
            if next_key not in best_cost or new_cost < best_cost[next_key]:
                best_cost[next_key] = new_cost
                parent[next_key] = key
                action_to[next_key] = successor.action
                priority = new_cost + calculate_heuristic(game_map, next_state)
                heapq.heappush(
                    frontier, (priority, new_cost, next(counter), next_state)
                )
        check_stop()

    if runtime is not None:
        runtime.mark_search_stopped()
    return None, None, expanded_nodes
>>>>>>> origin/feature/TV5-UCS+A_star_and_cost_calc
