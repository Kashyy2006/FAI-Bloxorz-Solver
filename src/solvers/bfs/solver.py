from collections import deque

from src.solvers.common.path import reconstruct_actions
from src.solvers.common.result import SolverResult
from src.solvers.common.boundary import run_search


def _search(game_map, start_state, *, state_key, is_goal, successors, runtime=None):
    """Return (actions, path cost, expansions) for a finite, valid state graph."""
    if is_goal(game_map, start_state):
        return [], 0, 0

    if runtime is not None:
        runtime.start()
    check_stop = runtime.check_stop if runtime is not None else lambda: None
    check_stop()
    start_key = state_key(start_state)
    frontier = deque([(start_state, 0)])
    parent = {start_key: None}
    action_to = {}
    expanded_nodes = 0

    while frontier:
        check_stop()
        state, path_cost = frontier.popleft()
        key = state_key(state)
        goal = is_goal(game_map, state)
        check_stop()
        if goal:
            if runtime is not None:
                runtime.mark_search_stopped()
            return (
                reconstruct_actions(parent, action_to, key),
                path_cost,
                expanded_nodes,
            )

        expanded_nodes += 1
        if runtime is not None:
            runtime.metrics.expanded_nodes = expanded_nodes
        next_states = successors(game_map, state)
        check_stop()
        for successor in next_states:
            check_stop()
            next_key = state_key(successor.state)
            if next_key in parent:
                continue
            parent[next_key] = key
            action_to[next_key] = successor.action
            frontier.append((successor.state, path_cost + successor.cost))
        check_stop()

    if runtime is not None:
        runtime.mark_search_stopped()
    return None, None, expanded_nodes


def solve_bfs(
    game_map, start_state, *, map_id, bridge_ids,
    state_key, is_goal, successors, validate_start_state,
    timeout_s=60.0, cancel_event=None,
) -> SolverResult:
    """Compatibility callback API; application code should use solve()."""
    return run_search(
        game_map, start_state, map_id=map_id, bridge_ids=bridge_ids,
        state_key=state_key, is_goal=is_goal, successors=successors,
        validate_start_state=validate_start_state, timeout_s=timeout_s,
        cancel_event=cancel_event, algorithm="BFS", search=_search,
    )


_solve_bfs = solve_bfs
