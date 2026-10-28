"""Pure state transitions, advanced game mechanics and canonical step costs."""

from __future__ import annotations

from .geometry import movement_pose as _candidate
from .map_loader import GameMap
from .models import Action, Mode, State, Status, Successor, TransitionResult

ACTION_ORDER = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT, Action.SWITCH)


def initial_state(game_map: GameMap) -> State:
    return State(Mode.UPRIGHT, (game_map.start,), bridges=tuple(b.initial_open for b in game_map.bridges))


def state_key(state: State) -> tuple:
    return state.mode.value, state.cells, state.active, state.bridges


def is_goal(game_map: GameMap, state: State) -> bool:
    return state.mode is Mode.UPRIGHT and state.cells[0] == game_map.goal



def _support_error(game_map, mode, cells, bridges):
    bridge_at = {cell: i for i, group in enumerate(game_map.bridges) for cell in group.cells}
    for row, col in sorted(cells):
        if not (0 <= row < game_map.rows and 0 <= col < game_map.cols):
            return "OUT_OF_BOUNDS"
        tile = game_map.tile_at((row, col))
        if tile == "void":
            return "VOID"
        if tile == "bridge" and not bridges[bridge_at[(row, col)]]:
            return "CLOSED_BRIDGE"
        if tile == "fragile" and mode is Mode.UPRIGHT:
            return "FRAGILE_UPRIGHT"
    return None


def validate_state(game_map: GameMap, state: State) -> None:
    """Validate a live, canonical snapshot against this map (including support)."""
    if not isinstance(state, State):
        raise ValueError("state: expected State")
    if len(state.bridges) != len(game_map.bridges):
        raise ValueError("state.bridges: wrong number of bridge flags")
    reason = _support_error(game_map, state.mode, state.cells, state.bridges)
    if reason:
        raise ValueError(f"state: unsupported placement ({reason})")


def _pressed(switch, mode, cells):
    if switch.type == "soft":
        return switch.cell in cells
    return mode == Mode.UPRIGHT and cells == (switch.cell,)


def _activated_switches(game_map, state, mode, cells):
    """One source for edge-trigger detection, before teleport or merging."""
    return tuple(s for s in game_map.switches
                 if not _pressed(s, state.mode, state.cells) and _pressed(s, mode, cells))


def transition(game_map: GameMap, state: State, action: str | Action) -> TransitionResult:
    validate_state(game_map, state)
    if is_goal(game_map, state):
        return TransitionResult(Status.INVALID, reason="ALREADY_WON")
    try:
        action = action if isinstance(action, Action) else Action(action)
    except (ValueError, TypeError):
        return TransitionResult(Status.INVALID, reason="UNKNOWN_ACTION")
    if action is Action.SWITCH:
        if state.mode is not Mode.SPLIT:
            return TransitionResult(Status.INVALID, reason="SWITCH_REQUIRES_SPLIT")
        return TransitionResult(Status.OK,
                                State(state.mode, state.cells, 1 - state.active, state.bridges))
    try:
        mode, cells, active = _candidate(state, action)
    except ValueError as exc:
        return TransitionResult(Status.INVALID, reason=str(exc))
    reason = _support_error(game_map, mode, cells, state.bridges)
    if reason:
        return TransitionResult(Status.LOST, reason=reason)
    activated = _activated_switches(game_map, state, mode, cells)
    flags = list(state.bridges)
    indices = {ident: i for i, ident in enumerate(game_map.bridge_ids)}
    events = []
    for switch in activated:
        events.append({"type": "SWITCH_ACTIVATED", "switch_id": switch.id})
        if switch.type == "split":
            mode = Mode.SPLIT
            cells = tuple(sorted(switch.destinations))
            chosen = switch.destinations[switch.active_destination]
            active = cells.index(chosen)
            events.append({"type": "BLOCK_SPLIT", "cells": [list(c) for c in cells], "active": active})
        else:
            for ident in switch.targets:
                i = indices[ident]
                before = flags[i]
                flags[i] = not before if switch.effect_mode == "toggle" else switch.open
                if flags[i] != before:
                    events.append({"type": "BRIDGE_CHANGED", "bridge_id": ident,
                                   "before": before, "after": flags[i]})
    flags = tuple(flags)
    reason = _support_error(game_map, mode, cells, flags)
    if reason:
        return TransitionResult(Status.LOST, reason=reason, events=tuple(events))
    if mode is Mode.SPLIT:
        (r1, c1), (r2, c2) = cells
        if abs(r1-r2) + abs(c1-c2) == 1:
            mode = Mode.HORIZONTAL if r1 == r2 else Mode.VERTICAL
            active = None
            events.append({"type": "BLOCK_MERGED", "mode": mode.value,
                           "cells": [list(c) for c in cells]})
    next_state = State(mode, cells, active, flags)
    status = Status.WON if is_goal(game_map, next_state) else Status.OK
    return TransitionResult(status, next_state, events=tuple(events))


def step_cost(game_map: GameMap, state: State, action: str | Action,
              next_state: State) -> int:
    """Compatibility API; costs.calc owns the shared 1 + 2*F + T formula."""
    from src.solvers.costs.calc import calculate_step_cost
    return calculate_step_cost(game_map, state, next_state, action)


def successors(game_map: GameMap, state: State) -> list[Successor]:
    if is_goal(game_map, state):
        return []
    results = []
    for action in ACTION_ORDER:
        result = transition(game_map, state, action)
        if result.status in (Status.OK, Status.WON) and result.next_state is not None:
            results.append(Successor(action, result.next_state,
                                     step_cost(game_map, state, action, result.next_state)))
    return results
