"""Shared engine boundary for GUI workers, benchmark bindings and all four algorithms."""
from dataclasses import asdict
import json
from pathlib import Path

from src.engine import (GameMap, State, is_goal, load_map, parse_map,
                        state_from_dict, state_key, state_to_dict, successors,
                        validate_state)
from src.solvers.astar.solver import _search as astar
from src.solvers.bfs.solver import _search as bfs
from src.solvers.common.result import SolverMetrics, SolverResult
from src.solvers.common.runtime import SearchRuntime, SearchStopped, validate_timeout
from src.solvers.dfs.solver import _search as dfs
from src.solvers.ucs.solver import _search as ucs

ALGORITHMS = {
    "BFS": bfs,
    "DFS": dfs,
    "UCS": ucs,
    "ASTAR": astar,
}


def solve(game_map, start_state, algorithm, timeout_s=60.0, cancel_event=None):
    metrics = SolverMetrics()
    result = SolverResult(
        map_id=None, algorithm=algorithm, status="ERROR",
        start_state=None, actions=None, metrics=metrics, timeout_s=None,
        heuristic="goal_indicator_v1" if algorithm == "ASTAR" else None,
    )
    runtime = None
    stage = "algorithm"
    try:
        if not isinstance(algorithm, str) or algorithm not in ALGORITHMS:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        stage = "game_map"
        if isinstance(game_map, GameMap):
            m = game_map
        elif isinstance(game_map, (str, Path)):
            m = load_map(game_map)
        else:
            m = parse_map(game_map)
        result.map_id = m.id
        stage = "timeout_s"
        result.timeout_s = validate_timeout(timeout_s)
        stage = "cancel_event"
        runtime = SearchRuntime(result.timeout_s, cancel_event, metrics)
        stage = "start_state"
        if isinstance(start_state, State):
            state = start_state
        elif isinstance(start_state, dict):
            snapshot = dict(start_state)
            if "bridges" not in snapshot and not m.bridge_ids:
                snapshot["bridges"] = {}
            elif isinstance(snapshot.get("bridges"), tuple):
                if len(snapshot["bridges"]) != len(m.bridge_ids):
                    raise ValueError("state.bridges: wrong number of bridge flags")
                snapshot["bridges"] = dict(zip(m.bridge_ids, snapshot["bridges"]))
            state = state_from_dict(m, snapshot)
        else:
            raise ValueError("start_state must be a State or snapshot dict")
        validate_state(m, state)
        serialized_start = state_to_dict(m, state)
        json.dumps(serialized_start, allow_nan=False)
        result.start_state = serialized_start
        stage = algorithm
        actions, cost, expanded = ALGORITHMS[algorithm](
            m, state, state_key=state_key, is_goal=is_goal,
            successors=successors, runtime=runtime,
        )
        result.status = "UNSOLVABLE" if actions is None else "SOLVED"
        metrics.expanded_nodes = expanded
        if actions is not None:
            result.actions = [action.value if hasattr(action, "value") else str(action)
                              for action in actions]
            metrics.solution_length = len(result.actions)
            metrics.solution_cost = cost
    except SearchStopped as stopped:
        result.status = stopped.status
    except Exception as error:
        result.status = "ERROR"
        result.error = f"{stage}: {type(error).__name__}: {error}"
    finally:
        if runtime is not None:
            try:
                runtime.finish()
            except Exception as error:
                result.status = "ERROR"
                cleanup_error = f"cleanup: {type(error).__name__}: {error}"
                result.error = f"{result.error}; {cleanup_error}" if result.error else cleanup_error

    if result.status != "SOLVED":
        result.actions = None
        metrics.solution_length = metrics.solution_cost = None
    if not isinstance(algorithm, str) or algorithm not in ALGORITHMS:
        return asdict(result)
    try:
        payload = result.to_dict()
        json.dumps(payload, allow_nan=False)
        return payload
    except Exception as error:
        result.status = "ERROR"
        result.actions = None
        metrics.solution_length = metrics.solution_cost = None
        serialization_error = f"result: {type(error).__name__}: {error}"
        result.error = f"{result.error}; {serialization_error}" if result.error else serialization_error
        return asdict(result)


def run_bfs(map_path, snapshot, *, timeout_s=60.0):
    return solve(map_path, snapshot, "BFS", timeout_s=timeout_s)


def run_dfs(map_path, snapshot, *, timeout_s=60.0):
    return solve(map_path, snapshot, "DFS", timeout_s=timeout_s)


def run_ucs(map_path, snapshot, *, timeout_s=60.0):
    return solve(map_path, snapshot, "UCS", timeout_s=timeout_s)


def run_astar(map_path, snapshot, *, timeout_s=60.0):
    return solve(map_path, snapshot, "ASTAR", timeout_s=timeout_s)

