"""Visual timing only; engine transitions remain instantaneous and authoritative."""
from dataclasses import dataclass
from src.engine.models import Mode

MOVE_DURATION = 0.24
SPLIT_DURATION = 0.85


@dataclass(frozen=True)
class BlockPose:
    """Visual-only failed placement; never used as an engine/search state."""
    mode: Mode
    cells: tuple[tuple[int, int], ...]
    active: int | None
    bridges: tuple[bool, ...]


def motion_duration(motion):
    return SPLIT_DURATION if any(e["type"] == "BLOCK_SPLIT" for e in motion.get("events", ())) else MOVE_DURATION


BRIDGE_DURATION = 0.38
FALL_DURATION = 0.7


class BridgeAnimator:
    def __init__(self):
        self.values = {}
        self.pending = {}

    def reset(self, game_map, state):
        self.values = dict(zip(game_map.bridge_ids, map(float, state.bridges)))
        self.pending.clear()

    @property
    def busy(self):
        return bool(self.pending)

    def trigger(self, events):
        # Multiple switches may alter a group in one step. Animate its final value.
        targets = {}
        for event in events:
            if event["type"] == "BRIDGE_CHANGED":
                targets[event["bridge_id"]] = float(event["after"])
        for ident, target in targets.items():
            start = self.values[ident]
            if start != target:
                self.pending[ident] = (start, target, 0.0)
            else:
                self.pending.pop(ident, None)

    def update(self, dt):
        for ident, (start, target, elapsed) in list(self.pending.items()):
            elapsed = min(BRIDGE_DURATION, elapsed + max(0.0, dt))
            t = elapsed / BRIDGE_DURATION
            eased = t * t * (3 - 2 * t)
            self.values[ident] = start + (target - start) * eased
            if elapsed >= BRIDGE_DURATION:
                del self.pending[ident]
            else:
                self.pending[ident] = (start, target, elapsed)

    def tile_levels(self, game_map):
        return {cell: self.values.get(group.id, float(group.initial_open))
                for group in game_map.bridges for cell in group.cells}
