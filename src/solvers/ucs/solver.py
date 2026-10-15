import heapq
from itertools import count


def reconstruct_actions(parent, action_to, goal_key):
    actions = []
    curr = goal_key
    while parent[curr] is not None:
        actions.append(action_to[curr])
        curr = parent[curr]
    actions.reverse()
    return actions


def _search(game_map, start_state, *, state_key, is_goal, successors):
    """Uniform Cost Search (Dijkstra's Algorithm variant for state space).

    Trả về (actions, path_cost, expanded_nodes).
    """
    if is_goal(game_map, start_state):
        return [], 0, 0

    start_key = state_key(start_state)
    counter = count()
    frontier = [(0, next(counter), start_state)]
    best_cost = {start_key: 0}
    parent = {start_key: None}
    action_to = {}
    expanded_nodes = 0
    visited = set()

    while frontier:
        cost, _, state = heapq.heappop(frontier)
        key = state_key(state)
        if key in visited:
            continue
        visited.add(key)
        if is_goal(game_map, state):
            return (
                reconstruct_actions(parent, action_to, key),
                cost,
                expanded_nodes,
            )
        expanded_nodes += 1

        for successor in successors(game_map, state):
            next_state = successor.state
            next_key = state_key(next_state)
            new_cost = cost + successor.cost
            if next_key not in best_cost or new_cost < best_cost[next_key]:
                best_cost[next_key] = new_cost
                parent[next_key] = key
                action_to[next_key] = successor.action
                heapq.heappush(frontier, (new_cost, next(counter), next_state))
    return None, None, expanded_nodes