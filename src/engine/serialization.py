"""Validated JSON snapshots for GUI, workers and solver replay."""
from .map_loader import GameMap
from .models import State
from .rules import validate_state


def state_to_dict(game_map: GameMap, state: State) -> dict:
    validate_state(game_map, state)
    return {"mode": state.mode.value, "cells": [list(c) for c in state.cells],
            "active": state.active, "bridges": dict(zip(game_map.bridge_ids, state.bridges))}


def state_from_dict(game_map: GameMap, data: dict) -> State:
    if not isinstance(data, dict) or set(data) != {"mode", "cells", "active", "bridges"}:
        raise ValueError("state: expected mode, cells, active, bridges")
    flags = data["bridges"]
    if not isinstance(flags, dict) or set(flags) != set(game_map.bridge_ids):
        raise ValueError("state.bridges: IDs do not match map")
    state = State(data["mode"], data["cells"], data["active"], tuple(flags[i] for i in game_map.bridge_ids))
    validate_state(game_map, state)
    return state
