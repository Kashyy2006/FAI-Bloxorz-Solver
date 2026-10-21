import heapq
import json
from itertools import count

from src.solvers.common.path import reconstruct_actions
from src.solvers.common.result import SolverMetrics, SolverResult, snapshot_to_dict
from src.solvers.common.runtime import SearchRuntime, SearchStopped, validate_timeout


<<<<<<< HEAD
def _search(game_map, start_state, *, state_key, is_goal, successors,
            runtime=None, heuristic=None):
    """Weighted search kernel; default heuristic is zero (UCS)."""
    if is_goal(game_map, start_state):
        return [], 0, 0
    if runtime is not None:
        runtime.start()
    check_stop = runtime.check_stop if runtime is not None else lambda: None
    check_stop()
    estimate = heuristic if heuristic is not None else lambda m, s: 0
=======
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
>>>>>>> origin/feature/TV5-UCS+A_star_and_cost_calc
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
<<<<<<< HEAD
        _, _, cost, state = heapq.heappop(frontier)
        key = state_key(state)
        if cost != best_cost[key] or cost >= expanded_cost.get(key, float("inf")):
            continue
=======
        cost, _, state = heapq.heappop(frontier)
        key = state_key(state)
        check_stop()
        if key in visited:
            continue
        visited.add(key)
>>>>>>> origin/feature/TV5-UCS+A_star_and_cost_calc
        goal = is_goal(game_map, state)
        check_stop()
        if goal:
            if runtime is not None:
                runtime.mark_search_stopped()
<<<<<<< HEAD
            return reconstruct_actions(parent, action_to, key), cost, expanded_nodes
        expanded_cost[key] = cost
        expanded_nodes += 1
        if runtime is not None:
            runtime.metrics.expanded_nodes = expanded_nodes
=======
            return (
                reconstruct_actions(parent, action_to, key),
                cost,
                expanded_nodes,
            )
        expanded_nodes += 1
        if runtime is not None:
            runtime.metrics.expanded_nodes = expanded_nodes

>>>>>>> origin/feature/TV5-UCS+A_star_and_cost_calc
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
<<<<<<< HEAD
                priority = new_cost + estimate(game_map, next_state)
                heapq.heappush(frontier, (priority, next(counter), new_cost, next_state))
=======
                heapq.heappush(frontier, (new_cost, next(counter), next_state))
>>>>>>> origin/feature/TV5-UCS+A_star_and_cost_calc
        check_stop()
    if runtime is not None:
        runtime.mark_search_stopped()
    return None, None, expanded_nodes
<<<<<<< HEAD
=======


def _solve_ucs(
    game_map, start_state, *, map_id, bridge_ids,
    state_key, is_goal, successors, validate_start_state,
    timeout_s=60.0, cancel_event=None,
) -> SolverResult:
    """Internal UCS boundary; engine validation and metadata are supplied explicitly."""
    metrics = SolverMetrics()
    result = SolverResult(
        map_id=None, algorithm="UCS", status="ERROR", start_state=None,
        actions=None, metrics=metrics, timeout_s=None,
    )
    runtime = None
    stage = "map_id"
    try:
        if not isinstance(map_id, str) or not map_id.strip():
            raise ValueError("map_id must be a non-empty string")
        result.map_id = map_id
        stage = "timeout_s"
        result.timeout_s = validate_timeout(timeout_s)
        stage = "cancel_event"
        runtime = SearchRuntime(result.timeout_s, cancel_event, metrics)
        stage = "callbacks"
        for name, callback in (
            ("state_key", state_key), ("is_goal", is_goal),
            ("successors", successors), ("validate_start_state", validate_start_state),
        ):
            if not callable(callback):
                raise ValueError(f"{name} must be callable")
        stage = "start_state"
        validate_start_state(game_map, start_state)
        snapshot = snapshot_to_dict(start_state, bridge_ids)
        json.dumps(snapshot, allow_nan=False)
        result.start_state = snapshot
        stage = "UCS"
        actions, cost, expanded = _search(
            game_map, start_state, state_key=state_key, is_goal=is_goal,
            successors=successors, runtime=runtime,
        )
        metrics.expanded_nodes = expanded
        result.status = "UNSOLVABLE" if actions is None else "SOLVED"
        result.actions = actions
        if actions is not None:
            metrics.solution_length = len(actions)
            metrics.solution_cost = cost
    except SearchStopped as stopped:
        result.status = stopped.status
    except Exception as exc:
        result.status = "ERROR"
        result.error = f"{stage}: {type(exc).__name__}: {exc}"
    finally:
        if runtime is not None:
            try:
                runtime.finish()
            except Exception as exc:
                result.status = "ERROR"
                cleanup_error = f"cleanup: {type(exc).__name__}: {exc}"
                result.error = f"{result.error}; {cleanup_error}" if result.error else cleanup_error

    if result.status != "SOLVED":
        result.actions = None
        metrics.solution_length = metrics.solution_cost = None
    try:
        json.dumps(result.to_dict(), allow_nan=False)
    except Exception as exc:
        result.status = "ERROR"
        result.actions = None
        metrics.solution_length = metrics.solution_cost = None
        serialization_error = f"result: {type(exc).__name__}: {exc}"
        result.error = f"{result.error}; {serialization_error}" if result.error else serialization_error
    return result
>>>>>>> origin/feature/TV5-UCS+A_star_and_cost_calc
