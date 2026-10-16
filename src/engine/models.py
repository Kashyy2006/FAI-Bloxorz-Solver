"""Immutable engine state and action/result models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

Coordinate = tuple[int, int]


class Mode(str, Enum):
    UPRIGHT = "UPRIGHT"
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"
    SPLIT = "SPLIT"


class Action(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    SWITCH = "SWITCH"


class Status(str, Enum):
    OK = "OK"
    WON = "WON"
    LOST = "LOST"
    INVALID = "INVALID"


@dataclass(frozen=True)
class State:
    """Canonical immutable state; cells are always ordered by (row, col)."""

    mode: Mode
    cells: tuple[Coordinate, ...]
    active: Optional[int] = None
    bridges: tuple[bool, ...] = ()

    def __post_init__(self) -> None:
        try:
            mode = self.mode if isinstance(self.mode, Mode) else Mode(self.mode)
        except ValueError as exc:
            raise ValueError(f"Unknown state mode: {self.mode!r}") from exc
        cells = tuple(sorted(tuple(cell) for cell in self.cells))
        if any(len(cell) != 2 or any(type(value) is not int for value in cell) for cell in cells):
            raise ValueError("Each cell coordinate must contain two integers")
        expected_count = 1 if mode is Mode.UPRIGHT else 2
        if len(cells) != expected_count:
            raise ValueError(f"{mode.value} requires {expected_count} cell(s)")
        if len(set(cells)) != len(cells):
            raise ValueError("State cells must be distinct")
        if mode is Mode.HORIZONTAL:
            (r1, c1), (r2, c2) = cells
            if r1 != r2 or c2 != c1 + 1:
                raise ValueError("HORIZONTAL cells must be adjacent in one row")
        elif mode is Mode.VERTICAL:
            (r1, c1), (r2, c2) = cells
            if c1 != c2 or r2 != r1 + 1:
                raise ValueError("VERTICAL cells must be adjacent in one column")
        elif mode is Mode.SPLIT:
            (r1, c1), (r2, c2) = cells
            if abs(r1 - r2) + abs(c1 - c2) == 1:
                raise ValueError("Adjacent split cubes must be merged")
            if type(self.active) is not int or self.active not in (0, 1):
                raise ValueError("SPLIT state active must be 0 or 1")
        elif self.active is not None:
            raise ValueError("Non-split states must have active=None")
        if mode is not Mode.SPLIT and self.active is not None:
            raise ValueError("Non-split states must have active=None")
        if any(type(value) is not bool for value in self.bridges):
            raise ValueError("Bridge states must be booleans")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "cells", cells)
        object.__setattr__(self, "bridges", tuple(self.bridges))


@dataclass(frozen=True)
class TransitionResult:
    status: Status
    next_state: Optional[State] = None
    reason: Optional[str] = None
    events: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True)
class Successor:
    action: Action
    state: State
    cost: int
