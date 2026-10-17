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


def _search(game_map, start_state, *, state_key, is_goal, successors,
            runtime=None, heuristic=None):
    """Weighted search kernel; default heuristic is zero (UCS)."""
    if is_goal(game_map, start_state):
        return [], 0, 0
    if runtime is not None:
        runtime.start()
    check_stop = runtime.check_stop if runtime is not None else lambda: None
    estimate = heuristic if heuristic is not None else lambda m, s: 0
    start_key = state_key(start_state)
    counter = count()
    frontier = [(estimate(game_map, start_state), next(counter), 0, start_state)]
    best_cost = {start_key: 0}
    parent = {start_key: None}
    action_to = {}
    expanded_nodes = 0
    expanded_cost = {}
    while frontier:
        check_stop()
        _, _, cost, state = heapq.heappop(frontier)
        key = state_key(state)
        if cost != best_cost[key] or cost >= expanded_cost.get(key, float("inf")):
            continue
        goal = is_goal(game_map, state)
        check_stop()
        if goal:
            if runtime is not None:
                runtime.mark_search_stopped()
            return reconstruct_actions(parent, action_to, key), cost, expanded_nodes
        expanded_cost[key] = cost
        expanded_nodes += 1
        if runtime is not None:
            runtime.metrics.expanded_nodes = expanded_nodes
        next_states = successors(game_map, state)
        check_stop()
        for successor in next_states:
            check_stop()
            next_state = successor.state
            next_key = state_key(next_state)
            new_cost = cost + successor.cost
            if new_cost < best_cost.get(next_key, float("inf")):
                best_cost[next_key] = new_cost
                parent[next_key] = key
                action_to[next_key] = successor.action
                priority = new_cost + estimate(game_map, next_state)
                heapq.heappush(frontier, (priority, next(counter), new_cost, next_state))
        check_stop()
    if runtime is not None:
        runtime.mark_search_stopped()
    return None, None, expanded_nodes
