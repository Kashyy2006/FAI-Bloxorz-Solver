"""Shared Bloxorz game engine (schema v1)."""

from .map_loader import Bridge, GameMap, Switch, load_map, parse_map
from .models import Action, Mode, State, Status, Successor, TransitionResult
from .rules import initial_state, is_goal, state_key, step_cost, successors, transition, validate_state

__all__ = [
    "Bridge", "Switch", "validate_state", "Action", "GameMap", "Mode", "State", "Status", "Successor",
    "TransitionResult", "initial_state", "is_goal", "load_map", "parse_map",
    "state_key", "step_cost", "successors", "transition",
]

from .serialization import state_from_dict, state_to_dict

__all__ += ["state_from_dict", "state_to_dict"]
