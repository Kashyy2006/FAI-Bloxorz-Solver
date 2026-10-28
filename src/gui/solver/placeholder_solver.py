"""Legacy import adapter. All searches now use the production engine dispatcher."""
from src.contracts import ALGORITHMS, ACTIONS, COST_MODEL
from src.solvers.solve import solve as _solve
from .result import make_result


def empty_result(game_map, start_state, algorithm, timeout_s):
    return make_result(game_map, start_state, algorithm, timeout_s,
                       "ERROR", "Search has not started")


def solve(game_map, start_state, algorithm, timeout_s=60.0, cancel_event=None, move_fn=None):
    """move_fn is retained for source compatibility; engine rules are authoritative."""
    return _solve(game_map, start_state, algorithm, timeout_s, cancel_event)
