"""One runtime, error and JSON boundary for callback APIs and the dispatcher."""
import json
from src.contracts import GOAL_INDICATOR
from src.solvers.costs.calc import heuristic_name
from .result import SolverMetrics, SolverResult, snapshot_to_dict
from .runtime import SearchRuntime, SearchStopped, validate_timeout

def run_search(
    game_map, start_state, *, map_id, bridge_ids,
    state_key, is_goal, successors, validate_start_state,
    timeout_s=60.0, cancel_event=None,
    algorithm="BFS", search=None, prepare_map=None, prepare_state=None,
) -> SolverResult:
    """Own validation, runtime, snapshots, errors and cleanup around a search kernel."""
    metrics = SolverMetrics()
    result = SolverResult(
        map_id=None, algorithm=algorithm, status="ERROR", start_state=None,
        actions=None, metrics=metrics, timeout_s=None,
    )
    runtime = None
    stage = "map_id"
    context = {"stage": stage}
    if algorithm == "ASTAR":
        result.heuristic = GOAL_INDICATOR
    try:
        if prepare_map is not None:
            game_map, map_id, bridge_ids = prepare_map(context, game_map)
        if not isinstance(map_id, str) or not map_id.strip():
            raise ValueError("map_id must be a non-empty string")
        result.map_id = map_id
        if algorithm == "ASTAR":
            mode = start_state.get("mode") if isinstance(start_state, dict) else getattr(start_state, "mode", None)
            result.heuristic = heuristic_name(game_map, mode == "SPLIT")
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
        if prepare_state is not None:
            start_state = prepare_state(game_map, start_state)
        validate_start_state(game_map, start_state)
        if algorithm == "ASTAR":
            result.heuristic = heuristic_name(game_map, start_state.mode == "SPLIT")
        snapshot = snapshot_to_dict(start_state, bridge_ids)
        json.dumps(snapshot, allow_nan=False)
        result.start_state = snapshot
        stage = algorithm
        actions, cost, expanded = search(
            game_map, start_state, state_key=state_key, is_goal=is_goal,
            successors=successors, runtime=runtime,
        )
        metrics.expanded_nodes = expanded
        result.status = "UNSOLVABLE" if actions is None else "SOLVED"
        result.actions = None if actions is None else [getattr(action, "value", action) for action in actions]
        if actions is not None:
            metrics.solution_length = len(actions)
            metrics.solution_cost = cost
    except SearchStopped as stopped:
        result.status = stopped.status
    except Exception as exc:
        result.status = "ERROR"
        if prepare_map is not None and result.map_id is None:
            stage = context["stage"]
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

