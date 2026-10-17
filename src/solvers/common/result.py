from dataclasses import asdict, dataclass, field
from math import isfinite

@dataclass

class SolverMetrics:
    search_time_s: float = 0.0
    peak_memory_bytes: int = 0
    expanded_nodes: int = 0
    solution_length: int | None = None
    solution_cost: int | None = None

@dataclass
class SolverResult:
    map_id: str | None
    algorithm: str
    status: str
    start_state: dict | None
    actions: list[str] | None
    metrics: SolverMetrics
    timeout_s: float | None
    heuristic: str | None = None
    error: str | None = None
    schema_version: int = field(default=1, init=False)
    cost_model: str = field(
      default="base1_fragile2_switch1_v1", init=False
    )


    def to_dict(self) -> dict:
        if self.algorithm not in {"BFS", "DFS", "UCS", "ASTAR"}:
            raise ValueError("Unknown algorithm")
        if self.status not in {
            "SOLVED", "UNSOLVABLE", "TIMEOUT", "CANCELLED", "ERROR"
        }:
            raise ValueError("Unknown solver status")
        if self.status != "ERROR" and any(
            value is None for value in (self.map_id, self.start_state, self.timeout_s)
        ):
            raise ValueError("Only ERROR may have unvalidated envelope fields")
        if self.map_id is not None and (
            not isinstance(self.map_id, str) or not self.map_id.strip()
        ):
            raise ValueError("map_id must be a non-empty string")
        if self.start_state is not None and not isinstance(self.start_state, dict):
            raise ValueError("start_state must be a snapshot object")
        if self.timeout_s is not None:
            try:
                valid_timeout = (
                    type(self.timeout_s) in (int, float)
                    and isfinite(self.timeout_s) and self.timeout_s > 0
                )
            except OverflowError:
                valid_timeout = False
            if not valid_timeout:
                raise ValueError("timeout_s must be a finite number > 0")
        if self.algorithm != "ASTAR" and self.heuristic is not None:
            raise ValueError("Only ASTAR may declare a heuristic")
        if self.algorithm == "ASTAR" and self.heuristic is None:
            raise ValueError("ASTAR must declare its heuristic")

        if self.status == "SOLVED":
            if self.actions is None:
                raise ValueError("SOLVED requires actions")
            if self.metrics.solution_length != len(self.actions):
                raise ValueError("solution_length must equal len(actions)")
            cost = self.metrics.solution_cost
            if type(cost) is not int or cost < len(self.actions):
                raise ValueError("SOLVED requires a valid solution_cost")
            if not self.actions and cost != 0:
                raise ValueError("An empty solution must have cost 0")
        elif (
            self.actions is not None
            or self.metrics.solution_length is not None
            or self.metrics.solution_cost is not None
        ):
            raise ValueError("A non-SOLVED result must have null solution fields")

        if self.status == "ERROR":
            if not isinstance(self.error, str) or not self.error.strip():
                raise ValueError("ERROR requires an error message")
        elif self.error is not None:
            raise ValueError("Only ERROR may contain an error message")

        return asdict(self)

def snapshot_to_dict(state, bridge_ids: tuple[str, ...]) -> dict:
    if any(not isinstance(bid, str) or not bid.strip() for bid in bridge_ids):
        raise ValueError("bridge_ids must contain non-empty strings")
    if bridge_ids != tuple(sorted(bridge_ids)):
        raise ValueError("bridge_ids must follow engine lexicographic order")
    if len(set(bridge_ids)) != len(bridge_ids):
        raise ValueError("bridge_ids must be unique")
    if len(bridge_ids) != len(state.bridges):
        raise ValueError("bridge_ids and state.bridges must have equal lengths")
    if any(type(value) is not bool for value in state.bridges):
        raise ValueError("Bridge states must be bool")

    return {
        "mode": state.mode,
        "cells": [list(cell) for cell in state.cells],
        "active": state.active,
        "bridges": dict(zip(bridge_ids, state.bridges)),
    }
