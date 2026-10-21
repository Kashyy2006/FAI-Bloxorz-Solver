"""Shared solver JSON schema; GUI/benchmark add request-specific checks."""
from src.engine.serialization import validate_snapshot
import math
import sys
from src.contracts import ALGORITHMS, ACTIONS, STATUSES, COST_MODEL, HEURISTICS

RESULT_FIELDS = frozenset(("schema_version", "map_id", "algorithm", "status", "start_state",
                           "actions", "metrics", "timeout_s", "cost_model", "heuristic", "error"))

def _number(value, name, *, integer=False, positive=False):
    valid = type(value) is int if integer else type(value) in (int, float)
    if (not valid or value > sys.float_info.max or not math.isfinite(value)
            or value < 0 or (positive and value == 0)):
        raise ValueError(f"{name}: expected a finite {'positive' if positive else 'nonnegative'} "
                         f"{'integer' if integer else 'number'}")


def validate_payload(raw):
    if not isinstance(raw, dict) or not RESULT_FIELDS <= raw.keys():
        raise ValueError("result: missing required contract fields")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise ValueError("schema_version: expected 1")
    status = raw["status"]
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("status: unknown solver status")
    if status != "ERROR" and any(raw[name] is None for name in ("map_id", "start_state", "timeout_s")):
        raise ValueError("Only ERROR may have unvalidated envelope fields")
    if raw["map_id"] is not None and (not isinstance(raw["map_id"], str) or not raw["map_id"].strip()):
        raise ValueError("map_id: expected a nonempty string")
    if raw["algorithm"] not in ALGORITHMS:
        raise ValueError("algorithm: unknown algorithm")
    if raw["timeout_s"] is not None:
        _number(raw["timeout_s"], "timeout_s", positive=True)
    if raw["cost_model"] != COST_MODEL:
        raise ValueError("cost_model: unsupported model")
    if ((raw["algorithm"] == "ASTAR" and (not isinstance(raw["heuristic"], str) or raw["heuristic"] not in HEURISTICS))
            or (raw["algorithm"] != "ASTAR" and raw["heuristic"] is not None)):
        raise ValueError("heuristic: does not match the algorithm contract")

    start = raw["start_state"]
    if not (status == "ERROR" and start is None):
        validate_snapshot(start)

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
    return raw
