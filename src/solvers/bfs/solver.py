from collections import deque
import json

from src.solvers.common.path import reconstruct_actions
from src.solvers.common.result import SolverMetrics, SolverResult, snapshot_to_dict
from src.solvers.common.runtime import SearchRuntime, SearchStopped, validate_timeout


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


def _solve_bfs(
    game_map, start_state, *, map_id, bridge_ids,
    state_key, is_goal, successors, validate_start_state,
    timeout_s=60.0, cancel_event=None,
) -> SolverResult:
    """Solve BFS using caller-supplied engine callbacks and metadata."""
    metrics = SolverMetrics()
    result = SolverResult(
        map_id=None, algorithm="BFS", status="ERROR", start_state=None,
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
        stage = "BFS"
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
