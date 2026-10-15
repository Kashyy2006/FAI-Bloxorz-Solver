from collections import deque

from src.solvers.common.path import reconstruct_actions


def _search(game_map, start_state, *, state_key, is_goal, successors):
    """Return (actions, path cost, expansions) for a finite, valid state graph."""
    # shortcut: no timeout/cancellation yet; add runtime guards in T4.
    if is_goal(game_map, start_state):
        return [], 0, 0

    start_key = state_key(start_state)
    frontier = deque([(start_state, 0)])
    parent = {start_key: None}
    action_to = {}
    expanded_nodes = 0

    while frontier:
        state, path_cost = frontier.popleft()
        key = state_key(state)
        if is_goal(game_map, state):
            return (
                reconstruct_actions(parent, action_to, key),
                path_cost,
                expanded_nodes,
            )

        expanded_nodes += 1
        for successor in successors(game_map, state):
            next_key = state_key(successor.state)
            if next_key in parent:
                continue
            parent[next_key] = key
            action_to[next_key] = successor.action
            frontier.append((successor.state, path_cost + successor.cost))

    return None, None, expanded_nodes
