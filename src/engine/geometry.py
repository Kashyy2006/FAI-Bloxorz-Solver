"""Map-independent movement geometry, shared by rules and visual previews."""
from .models import Action, Mode, State

def movement_pose(state: State, action: Action) -> tuple[Mode, tuple[tuple[int, int], ...], int | None]:
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
    return Mode.SPLIT, cells, active

