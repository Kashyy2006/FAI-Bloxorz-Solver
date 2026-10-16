"""Pure state transitions and shared basic-game helpers."""

from __future__ import annotations

from .map_loader import GameMap
from .models import Action, Mode, State, Status, Successor, TransitionResult

ACTION_ORDER = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT, Action.SWITCH)


def initial_state(game_map: GameMap) -> State:
    return State(Mode.UPRIGHT, (game_map.start,))


def state_key(state: State) -> tuple:
    return state.mode.value, state.cells, state.active, state.bridges


def is_goal(game_map: GameMap, state: State) -> bool:
    return state.mode is Mode.UPRIGHT and state.cells[0] == game_map.goal


def _candidate(state: State, action: Action) -> tuple[Mode, tuple[tuple[int, int], ...], int | None]:
    if state.mode is Mode.UPRIGHT:
        row, col = state.cells[0]
        moves = {
            Action.UP: (Mode.VERTICAL, ((row - 2, col), (row - 1, col))),
            Action.DOWN: (Mode.VERTICAL, ((row + 1, col), (row + 2, col))),
            Action.LEFT: (Mode.HORIZONTAL, ((row, col - 2), (row, col - 1))),
            Action.RIGHT: (Mode.HORIZONTAL, ((row, col + 1), (row, col + 2))),
        }
        mode, cells = moves[action]
        return mode, cells, None
    if state.mode is Mode.HORIZONTAL:
        row, col = state.cells[0]
        moves = {
            Action.UP: (Mode.HORIZONTAL, ((row - 1, col), (row - 1, col + 1))),
            Action.DOWN: (Mode.HORIZONTAL, ((row + 1, col), (row + 1, col + 1))),
            Action.LEFT: (Mode.UPRIGHT, ((row, col - 1),)),
            Action.RIGHT: (Mode.UPRIGHT, ((row, col + 2),)),
        }
        mode, cells = moves[action]
        return mode, cells, None
    if state.mode is Mode.VERTICAL:
        row, col = state.cells[0]
        moves = {
            Action.UP: (Mode.UPRIGHT, ((row - 1, col),)),
            Action.DOWN: (Mode.UPRIGHT, ((row + 2, col),)),
            Action.LEFT: (Mode.VERTICAL, ((row, col - 1), (row + 1, col - 1))),
            Action.RIGHT: (Mode.VERTICAL, ((row, col + 1), (row + 1, col + 1))),
        }
        mode, cells = moves[action]
        return mode, cells, None
    assert state.mode is Mode.SPLIT and state.active in (0, 1)
    row, col = state.cells[state.active]
    delta = {Action.UP: (-1, 0), Action.DOWN: (1, 0),
             Action.LEFT: (0, -1), Action.RIGHT: (0, 1)}[action]
    moved = (row + delta[0], col + delta[1])
    other = state.cells[1 - state.active]
    if moved == other:
        raise ValueError("CUBE_COLLISION")
    cells = tuple(sorted((moved, other)))
    active = cells.index(moved)
    (r1, c1), (r2, c2) = cells
    if r1 == r2 and c2 == c1 + 1:
        return Mode.HORIZONTAL, cells, None
    if c1 == c2 and r2 == r1 + 1:
        return Mode.VERTICAL, cells, None
    return Mode.SPLIT, cells, active


def _support_error(game_map: GameMap, mode: Mode,
                   cells: tuple[tuple[int, int], ...]) -> str | None:
    for row, col in cells:
        if not (0 <= row < game_map.rows and 0 <= col < game_map.cols):
            return "OUT_OF_BOUNDS"
        tile = game_map.tile_at((row, col))
        if tile == "void":
            return "VOID"
        if tile == "fragile" and mode is Mode.UPRIGHT:
            return "FRAGILE_UPRIGHT"
    return None


def transition(game_map: GameMap, state: State, action: str | Action) -> TransitionResult:
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
    reason = _support_error(game_map, mode, cells)
    if reason:
        return TransitionResult(Status.LOST, reason=reason)
    next_state = State(mode, cells, active, state.bridges)
    status = Status.WON if is_goal(game_map, next_state) else Status.OK
    return TransitionResult(status, next_state)


def step_cost(game_map: GameMap, state: State, action: str | Action,
              next_state: State) -> int:
    """Shared v1 cost; switch triggers are zero in this basic release."""
    action = action if isinstance(action, Action) else Action(action)
    newly_occupied_fragile = sum(
        game_map.tile_at(cell) == "fragile"
        for cell in set(next_state.cells) - set(state.cells)
    )
    return 1 + 2 * newly_occupied_fragile


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
