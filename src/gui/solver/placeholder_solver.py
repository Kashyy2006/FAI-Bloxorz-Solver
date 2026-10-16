"""Temporary solver so the solver GUI can be built before src/solvers is ready.

- Output follows docs/contracts/solver.md (status, actions, metrics, ...).
- Uses the manual GUI's temporary move function, so it only knows
  floor / void / goal / fragile (no bridges, switches or split yet).
- Replace by passing the real ``solve`` (members 4/5) as ``solve_fn`` to
  ``SolverController`` once the shared engine is integrated.
"""

import heapq
import itertools
import time
import tracemalloc

ACTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
ALGORITHMS = ("BFS", "DFS", "UCS", "ASTAR")
COST_MODEL = "base1_fragile2_switch1_v1"


def empty_result(game_map, start_state, algorithm, timeout_s):
    """Result skeleton with every field required by the contract."""
    return {
        "schema_version": 1,
        "map_id": game_map.get("id"),
        "algorithm": algorithm,
        "status": "ERROR",
        "start_state": {
            "mode": start_state["mode"],
            "cells": [list(cell) for cell in start_state["cells"]],
            "active": start_state.get("active"),
            "bridges": {},
        },
        "actions": None,
        "metrics": {
            "search_time_s": 0.0,
            "peak_memory_bytes": 0,
            "expanded_nodes": 0,
            "solution_length": None,
            "solution_cost": None,
        },
        "timeout_s": timeout_s,
        "cost_model": COST_MODEL,
        "heuristic": "goal_indicator_v1" if algorithm == "ASTAR" else None,
        "error": None,
    }


def _key(state):
    return (state["mode"], tuple(sorted(tuple(c) for c in state["cells"])),
            state.get("active"))


def _is_goal(grid, state):
    if state["mode"] != "UPRIGHT":
        return False
    row, col = state["cells"][0]
    return grid[row][col] == "goal"


def _successors(grid, state, move_fn):
    old_cells = {tuple(cell) for cell in state["cells"]}
    result = []
    for action in ACTIONS:
        nxt = move_fn(state, action, grid)
        if nxt is None:
            continue
        if nxt["mode"] == "UPRIGHT":
            row, col = nxt["cells"][0]
            if grid[row][col] == "fragile":
                continue  # LOST: standing upright on a fragile tile
        fragile = sum(1 for r, c in nxt["cells"]
                      if (r, c) not in old_cells and grid[r][c] == "fragile")
        result.append((action, nxt, 1 + 2 * fragile))
    return result


def _path(parents, key):
    actions = []
    while parents[key] is not None:
        key, action = parents[key]
        actions.append(action)
    return actions[::-1]


def _search(grid, start, algorithm, deadline, cancel_event, metrics, move_fn):
    counter = itertools.count()
    weighted = algorithm in ("UCS", "ASTAR")

    def priority(g, state, depth):
        n = next(counter)
        if algorithm == "BFS":
            return (depth, n)
        if algorithm == "DFS":
            return (-n,)  # LIFO
        if algorithm == "UCS":
            return (g, n)
        return (g + (0 if _is_goal(grid, state) else 1), n)

    start_key = _key(start)
    parents = {start_key: None}
    best_g = {start_key: 0}
    frontier = [(priority(0, start, 0), 0, 0, start)]

    while frontier:
        if cancel_event is not None and cancel_event.is_set():
            return "CANCELLED", None, None
        if time.perf_counter() > deadline:
            return "TIMEOUT", None, None
        _, g, depth, state = heapq.heappop(frontier)
        key = _key(state)
        if weighted and g > best_g[key]:
            continue  # stale entry
        if _is_goal(grid, state):
            return "SOLVED", _path(parents, key), g
        metrics["expanded_nodes"] += 1
        successors = _successors(grid, state, move_fn)
        if algorithm == "DFS":
            successors.reverse()  # so UP is popped first
        for action, nxt, step in successors:
            nkey, ng = _key(nxt), g + step
            if weighted:
                if ng >= best_g.get(nkey, float("inf")):
                    continue
            elif nkey in parents:
                continue
            parents[nkey] = (key, action)
            best_g[nkey] = ng
            heapq.heappush(frontier, (priority(ng, nxt, depth + 1), ng, depth + 1, nxt))
    return "UNSOLVABLE", None, None


def solve(game_map, start_state, algorithm, timeout_s=60.0, cancel_event=None,
          move_fn=None):
    result = empty_result(game_map, start_state, algorithm, timeout_s)
    if algorithm not in ALGORITHMS:
        result["error"] = f"Unknown algorithm: {algorithm}"
        return result
    if move_fn is None:
        result["error"] = "Placeholder solver needs a move function"
        return result

    metrics = result["metrics"]
    tracemalloc.start()
    started = time.perf_counter()
    try:
        status, actions, cost = _search(game_map["grid"], start_state, algorithm,
                                        started + timeout_s, cancel_event,
                                        metrics, move_fn)
        result["status"] = status
        if status == "SOLVED":
            result["actions"] = actions
            metrics["solution_length"] = len(actions)
            metrics["solution_cost"] = cost
    except Exception as error:  # report instead of crashing the worker thread
        result["status"] = "ERROR"
        result["error"] = str(error)
    finally:
        metrics["search_time_s"] = time.perf_counter() - started
        metrics["peak_memory_bytes"] = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
    return result
