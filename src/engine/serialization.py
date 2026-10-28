"""Validated JSON snapshots for GUI, workers and solver replay."""
from .map_loader import GameMap
from .models import State, Mode
from .rules import validate_state


def state_to_dict(game_map: GameMap, state: State) -> dict:
    validate_state(game_map, state)
    return snapshot_to_dict(state, game_map.bridge_ids)


def state_from_dict(game_map: GameMap, data: dict) -> State:
    if not isinstance(data, dict) or set(data) != {"mode", "cells", "active", "bridges"}:
        raise ValueError("state: expected mode, cells, active, bridges")
    flags = data["bridges"]
    if not isinstance(flags, dict) or set(flags) != set(game_map.bridge_ids):
        raise ValueError("state.bridges: IDs do not match map")
    state = State(data["mode"], data["cells"], data["active"], tuple(flags[i] for i in game_map.bridge_ids))
    validate_state(game_map, state)
    return state


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

    snapshot = {
        "mode": getattr(state.mode, "value", state.mode),
        "cells": [list(cell) for cell in state.cells],
        "active": state.active,
        "bridges": dict(zip(bridge_ids, state.bridges)),
    }
    validate_snapshot(snapshot)
    return snapshot


def normalize_snapshot(data, bridge_ids):
    """Own a JSON-compatible snapshot; flags always use sorted bridge IDs."""
    if (not isinstance(data, dict) or not {"mode", "cells"} <= data.keys()
            or not data.keys() <= {"mode", "cells", "active", "bridges"}):
        raise ValueError("state: expected mode, cells, active, bridges")
    flags = data.get("bridges", {})
    if not isinstance(flags, dict):
        if len(flags) != len(bridge_ids):
            raise ValueError("state.bridges: wrong number of bridge flags")
        flags = dict(zip(bridge_ids, flags))
    if set(flags) != set(bridge_ids) or any(type(flag) is not bool for flag in flags.values()):
        raise ValueError("state.bridges: IDs/boolean flags do not match map")
    snapshot = {"mode": getattr(data["mode"], "value", data["mode"]),
            "cells": [list(cell) for cell in data["cells"]], "active": data.get("active"),
            "bridges": {bid: flags[bid] for bid in bridge_ids}}

    validate_snapshot(snapshot)
    return snapshot


def validate_snapshot(snapshot):
    """Structural wire checks; placement and canonical geometry belong to State/engine."""
    if not isinstance(snapshot, dict) or set(snapshot) != {"mode", "cells", "active", "bridges"}:
        raise ValueError("start_state: expected mode, cells, active, bridges")
    if not isinstance(snapshot["mode"], str) or snapshot["mode"] not in tuple(m.value for m in Mode):
        raise ValueError("start_state.mode: unknown block mode")
    cells = snapshot["cells"]
    if (not isinstance(cells, list) or not cells
            or any(not isinstance(cell, list) or len(cell) != 2
                   or any(type(n) is not int for n in cell) for cell in cells)):
        raise ValueError("start_state.cells: expected integer coordinate pairs")
    active = snapshot["active"]
    if active is not None and (type(active) is not int or active not in (0, 1)):
        raise ValueError("start_state.active: expected null, 0 or 1")
    bridges = snapshot["bridges"]
    if (not isinstance(bridges, dict)
            or any(not isinstance(k, str) or not k.strip() or type(v) is not bool for k, v in bridges.items())):
        raise ValueError("start_state.bridges: expected an object of boolean flags")
