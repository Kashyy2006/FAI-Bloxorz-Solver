"""Shared engine boundary for GUI workers, benchmark bindings and all four algorithms."""
from dataclasses import asdict
from src.contracts import ALGORITHMS as ALGORITHM_NAMES
from pathlib import Path

from src.engine import (GameMap, State, is_goal, load_map, parse_map,
                        state_from_dict, state_key, successors,
                        validate_state)
from src.solvers.astar.solver import _search as astar
from src.solvers.bfs.solver import _search as bfs
from src.solvers.common.boundary import run_search
from src.engine.serialization import normalize_snapshot
from src.solvers.dfs.solver import _search as dfs
from src.solvers.ucs.solver import _search as ucs

ALGORITHMS = dict(zip(ALGORITHM_NAMES, (bfs, dfs, ucs, astar), strict=True))


def solve(game_map, start_state, algorithm, timeout_s=60.0, cancel_event=None):
    """Public application API: normalize map/snapshot, run a kernel, return JSON."""
    def prepare_map(context, value):
        context["stage"] = "algorithm"
        if not isinstance(algorithm, str) or algorithm not in ALGORITHMS:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        context["stage"] = "game_map"
        if isinstance(value, GameMap):
            model = value
        elif isinstance(value, (str, Path)):
            model = load_map(value)
        else:
            model = parse_map(value)
        return model, model.id, model.bridge_ids

    def prepare_state(model, value):
        if isinstance(value, State):
            return value
        if not isinstance(value, dict):
            raise ValueError("start_state must be a State or snapshot dict")
        return state_from_dict(model, normalize_snapshot(value, model.bridge_ids))

    result = run_search(
        game_map, start_state, map_id=None, bridge_ids=(),
        state_key=state_key, is_goal=is_goal, successors=successors,
        validate_start_state=validate_state, timeout_s=timeout_s, cancel_event=cancel_event,
        algorithm=algorithm, search=ALGORITHMS.get(algorithm) if isinstance(algorithm, str) else None,
        prepare_map=prepare_map, prepare_state=prepare_state,
    )
    return asdict(result)


def run_bfs(map_path, snapshot, *, timeout_s=60.0):
    return solve(map_path, snapshot, "BFS", timeout_s=timeout_s)


def run_dfs(map_path, snapshot, *, timeout_s=60.0):
    return solve(map_path, snapshot, "DFS", timeout_s=timeout_s)


def run_ucs(map_path, snapshot, *, timeout_s=60.0):
    return solve(map_path, snapshot, "UCS", timeout_s=timeout_s)


def run_astar(map_path, snapshot, *, timeout_s=60.0):
    return solve(map_path, snapshot, "ASTAR", timeout_s=timeout_s)

