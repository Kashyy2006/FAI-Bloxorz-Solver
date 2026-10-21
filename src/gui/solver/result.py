"""Check the solver data contract at the GUI boundary, not path correctness."""

import copy
import json
import math
import sys

ACTIONS = frozenset(("UP", "DOWN", "LEFT", "RIGHT", "SWITCH"))
STATUSES = frozenset(("SOLVED", "UNSOLVABLE", "TIMEOUT", "CANCELLED", "ERROR"))
COST_MODEL = "base1_fragile2_switch1_v1"


def state_to_json(game_map, state):
    """Copy a GUI state; tuple bridge flags follow sorted map bridge IDs."""
    bridges = state.get("bridges", {})
    if not isinstance(bridges, dict):
        ids = sorted(bridge["id"] for bridge in game_map.get("bridges", []))
        if len(ids) != len(bridges):
            raise ValueError("start_state.bridges: wrong number of bridge flags")
        bridges = dict(zip(ids, bridges))
    return {
        "mode": state.get("mode"),
        "cells": [list(cell) for cell in state.get("cells", [])],
        "active": state.get("active"),
        "bridges": copy.deepcopy(bridges),
    }


def make_result(game_map, state, algorithm, timeout_s, status, error=None):
    """Full contract envelope for GUI-generated cancellation/errors."""
    return {
        "schema_version": 1, "map_id": game_map.get("id"),
        "algorithm": algorithm, "status": status,
        "start_state": state_to_json(game_map, state), "actions": None,
        "metrics": {"search_time_s": 0.0, "peak_memory_bytes": 0,
                    "expanded_nodes": 0, "solution_length": None, "solution_cost": None},
        "timeout_s": timeout_s, "cost_model": COST_MODEL,
        "heuristic": "goal_indicator_v1" if algorithm == "ASTAR" else None,
        "error": error,
    }


def _number(value, name, *, integer=False, positive=False):
    valid = type(value) is int if integer else type(value) in (int, float)
    if (not valid or value > sys.float_info.max or not math.isfinite(value)
            or value < 0 or (positive and value == 0)):
        raise ValueError(f"{name}: expected a finite {'positive' if positive else 'nonnegative'} "
                         f"{'integer' if integer else 'number'}")


def validate_result(raw, game_map, state, algorithm, timeout_s,
                    supported_actions=ACTIONS):
    """Return an owned dict, or raise ValueError with a field-level reason.

    Accept a decoded object or JSON text; reject missing/invalid measurements
    and results belonging to another solve. Path validation belongs to the engine.
    """
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, RecursionError) as error:
            raise ValueError(f"result: invalid JSON ({error})") from error
    if not isinstance(raw, dict):
        raise ValueError("result: expected an object")
    required = set(make_result(game_map, state, algorithm, timeout_s, "ERROR"))
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"result: missing fields {', '.join(sorted(missing))}")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise ValueError("schema_version: expected 1")
    status = raw["status"]
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("status: unknown solver status")
    if not (status == "ERROR" and raw["map_id"] is None):
        if not isinstance(raw["map_id"], str) or raw["map_id"] != game_map.get("id"):
            raise ValueError("map_id: does not match the current solve")
    if raw["algorithm"] != algorithm:
        raise ValueError("algorithm: does not match the current solve")
    if not (status == "ERROR" and raw["timeout_s"] is None):
        _number(raw["timeout_s"], "timeout_s", positive=True)
        if raw["timeout_s"] != timeout_s:
            raise ValueError("timeout_s: does not match the current solve")
    if raw["cost_model"] != COST_MODEL:
        raise ValueError("cost_model: unsupported model")
    heuristic = "goal_indicator_v1" if algorithm == "ASTAR" else None
    if raw["heuristic"] != heuristic:
        raise ValueError("heuristic: does not match the algorithm contract")

    start = raw["start_state"]
    if not (status == "ERROR" and start is None):
        if not isinstance(start, dict) or set(start) != {"mode", "cells", "active", "bridges"}:
            raise ValueError("start_state: expected mode, cells, active, bridges")
        cells = start["cells"]
        if (not isinstance(cells, list) or not cells
                or any(not isinstance(cell, list) or len(cell) != 2
                       or any(type(n) is not int for n in cell) for cell in cells)):
            raise ValueError("start_state.cells: expected integer coordinate pairs")
        active = start["active"]
        if active is not None and (type(active) is not int or active not in (0, 1)):
            raise ValueError("start_state.active: expected null, 0 or 1")
        bridges = start["bridges"]
        if (not isinstance(bridges, dict)
                or any(not isinstance(k, str) or type(v) is not bool for k, v in bridges.items())):
            raise ValueError("start_state.bridges: expected an object of boolean flags")
        if start != state_to_json(game_map, state):
            raise ValueError("start_state: does not match the current solve snapshot")

    metrics = raw["metrics"]
    names = {"search_time_s", "peak_memory_bytes", "expanded_nodes",
             "solution_length", "solution_cost"}
    if not isinstance(metrics, dict) or not names <= metrics.keys():
        raise ValueError("metrics: missing required measurements")
    _number(metrics["search_time_s"], "metrics.search_time_s")
    for name in ("peak_memory_bytes", "expanded_nodes"):
        _number(metrics[name], f"metrics.{name}", integer=True)
    if status == "SOLVED":
        actions = raw["actions"]
        if not isinstance(actions, list):
            raise ValueError("actions: SOLVED requires an array")
        for action in actions:
            if not isinstance(action, str) or action not in ACTIONS:
                raise ValueError("actions: unknown action")
            if action not in supported_actions:
                raise ValueError(f"actions: replay does not support {action}")
        for name in ("solution_length", "solution_cost"):
            _number(metrics[name], f"metrics.{name}", integer=True)
        if metrics["solution_length"] != len(actions):
            raise ValueError("metrics.solution_length: does not match actions")
        if metrics["solution_cost"] < len(actions):
            raise ValueError("metrics.solution_cost: less than the number of actions")
        if not actions and (metrics["solution_cost"] or metrics["expanded_nodes"]):
            raise ValueError("metrics: an already solved state requires zero cost/expanded")
    elif (raw["actions"] is not None or metrics["solution_length"] is not None
          or metrics["solution_cost"] is not None):
        raise ValueError("actions/solution_length/solution_cost: must be null unless SOLVED")
    if status == "ERROR":
        if not isinstance(raw["error"], str) or not raw["error"].strip():
            raise ValueError("error: ERROR requires a nonempty message")
    elif raw["error"] is not None:
        raise ValueError("error: must be null unless ERROR")
    return copy.deepcopy(raw)
