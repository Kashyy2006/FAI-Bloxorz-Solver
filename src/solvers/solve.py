"""Shared engine boundary for GUI workers and all four algorithms."""
from src.engine import (GameMap, State, parse_map, state_from_dict, state_to_dict,
                        state_key, is_goal, successors, validate_state)
from src.solvers.bfs.solver import _search as bfs
from src.solvers.dfs.solver import _search as dfs
from src.solvers.ucs.solver import _search as ucs
from src.solvers.astar.solver import _search as astar
from src.solvers.common.result import SolverMetrics, SolverResult
from src.solvers.common.runtime import SearchRuntime, SearchStopped, validate_timeout


def solve(game_map, start_state, algorithm, timeout_s=60.0, cancel_event=None):
    metrics = SolverMetrics()
    result = SolverResult(map_id=None, algorithm=algorithm, status="ERROR",
                          start_state=None, actions=None, metrics=metrics, timeout_s=None,
                          heuristic="goal_indicator_v1" if algorithm == "ASTAR" else None)
    runtime = None
    try:
        algorithms = {"BFS": bfs, "DFS": dfs, "UCS": ucs, "ASTAR": astar}
        if algorithm not in algorithms:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        m = game_map if isinstance(game_map, GameMap) else parse_map(game_map)
        result.map_id = m.id
        if isinstance(start_state, State):
            state = start_state
        else:
            snapshot = dict(start_state)
            snapshot.setdefault("bridges", {})
            state = state_from_dict(m, snapshot)
        validate_state(m, state)
        result.start_state = state_to_dict(m, state)
        result.timeout_s = validate_timeout(timeout_s)
        runtime = SearchRuntime(result.timeout_s, cancel_event, metrics)
        if not is_goal(m, state):
            runtime.check_stop()
        actions, cost, expanded = algorithms[algorithm](
            m, state, state_key=state_key, is_goal=is_goal, successors=successors, runtime=runtime)
        result.status = "UNSOLVABLE" if actions is None else "SOLVED"
        metrics.expanded_nodes = expanded
        if actions is not None:
            result.actions = [action.value for action in actions]
            metrics.solution_length = len(actions)
            metrics.solution_cost = cost
    except SearchStopped as stopped:
        result.status = stopped.status
    except Exception as error:
        result.status = "ERROR"
        result.error = f"{type(error).__name__}: {error}"
    finally:
        if runtime is not None:
            runtime.finish()
    if algorithm not in {"BFS", "DFS", "UCS", "ASTAR"}:
        from dataclasses import asdict
        return asdict(result)
    return result.to_dict()
