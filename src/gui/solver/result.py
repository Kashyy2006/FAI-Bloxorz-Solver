"""Check the solver data contract at the GUI boundary, not path correctness."""

import copy
import json

from src.contracts import ACTIONS, STATUSES, COST_MODEL
from src.engine.serialization import normalize_snapshot
from src.solvers.common.schema import validate_payload
from src.solvers.costs.calc import heuristic_name
from src.engine import parse_map


def state_to_json(game_map, state):
    ids = tuple(sorted(bridge["id"] for bridge in game_map.get("bridges", [])))
    return normalize_snapshot(state, ids)


def result_heuristic(game_map, state, algorithm):
    if algorithm != "ASTAR":
        return None
    return heuristic_name(parse_map(game_map), state.get("mode") == "SPLIT")


def make_result(game_map, state, algorithm, timeout_s, status, error=None):
    """Full contract envelope for GUI-generated cancellation/errors."""
    return {
        "schema_version": 1, "map_id": game_map.get("id"),
        "algorithm": algorithm, "status": status,
        "start_state": state_to_json(game_map, state), "actions": None,
        "metrics": {"search_time_s": 0.0, "peak_memory_bytes": 0,
                    "expanded_nodes": 0, "solution_length": None, "solution_cost": None},
        "timeout_s": timeout_s, "cost_model": COST_MODEL,
        "heuristic": result_heuristic(game_map, state, algorithm),
        "error": error,
    }


def validate_result(raw, game_map, state, algorithm, timeout_s, supported_actions=ACTIONS):
    """Validate the shared schema plus identity, snapshot and replay capabilities."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, RecursionError) as error:
            raise ValueError(f"result: invalid JSON ({error})") from error
    validate_payload(raw)
    for name, expected in (("map_id", game_map.get("id")), ("timeout_s", timeout_s),
                           ("start_state", state_to_json(game_map, state))):
        if raw[name] != expected and not (raw["status"] == "ERROR" and raw[name] is None):
            raise ValueError(f"{name}: does not match the current solve snapshot")
    if raw["algorithm"] != algorithm:
        raise ValueError("algorithm: does not match the current solve snapshot")
    if raw["heuristic"] != result_heuristic(game_map, state, algorithm):
        raise ValueError("heuristic: does not match the selected strategy")
    for action in raw["actions"] or []:
        if action not in supported_actions:
            raise ValueError(f"actions: replay does not support {action}")
    return copy.deepcopy(raw)
