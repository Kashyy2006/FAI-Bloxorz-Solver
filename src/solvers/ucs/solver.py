import heapq
from itertools import count

from src.solvers.common.path import reconstruct_actions
from src.solvers.common.result import SolverResult
from src.solvers.common.boundary import run_search


def _search(game_map, start_state, *, state_key, is_goal, successors, runtime=None):
    """Uniform Cost Search (Dijkstra's Algorithm variant for state space).

    Trả về (actions, path_cost, expanded_nodes).
    """
    if is_goal(game_map, start_state):
        return [], 0, 0

    if runtime is not None:
        runtime.start()
    check_stop = runtime.check_stop if runtime is not None else lambda: None
    check_stop()
    start_key = state_key(start_state)
    counter = count()
    frontier = [(0, next(counter), start_state)]
    best_cost = {start_key: 0}
    parent = {start_key: None}
    action_to = {}
    expanded_nodes = 0
    while frontier:
        check_stop()
        cost, _, state = heapq.heappop(frontier)
        key = state_key(state)
        check_stop()
        # A cheaper entry may have replaced this queued path.
        if cost != best_cost[key]:
            continue
        goal = is_goal(game_map, state)
        check_stop()
        if goal:
            if runtime is not None:
                runtime.mark_search_stopped()
            return (
                reconstruct_actions(parent, action_to, key),
                cost,
                expanded_nodes,
            )
        expanded_nodes += 1
        if runtime is not None:
            runtime.metrics.expanded_nodes = expanded_nodes

        next_states = successors(game_map, state)
        check_stop()
        for successor in next_states:
            check_stop()
            next_state = successor.state
            next_key = state_key(next_state)
            check_stop()
            new_cost = cost + successor.cost
            if new_cost < best_cost.get(next_key, float("inf")):
                best_cost[next_key] = new_cost
                parent[next_key] = key
                action_to[next_key] = successor.action
                heapq.heappush(frontier, (new_cost, next(counter), next_state))
        check_stop()
    if runtime is not None:
        runtime.mark_search_stopped()
    return None, None, expanded_nodes


def _solve_ucs(
    game_map, start_state, *, map_id, bridge_ids,
    state_key, is_goal, successors, validate_start_state,
    timeout_s=60.0, cancel_event=None,
) -> SolverResult:
    """Compatibility callback API; application code should use solve()."""
    return run_search(
        game_map, start_state, map_id=map_id, bridge_ids=bridge_ids,
        state_key=state_key, is_goal=is_goal, successors=successors,
        validate_start_state=validate_start_state, timeout_s=timeout_s,
        cancel_event=cancel_event, algorithm="UCS", search=_search,
    )
