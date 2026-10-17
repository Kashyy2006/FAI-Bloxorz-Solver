"""A* with a teleport-safe goal-indicator heuristic."""
from src.solvers.ucs.solver import _search as weighted_search


def _search(game_map, start_state, *, state_key, is_goal, successors, runtime=None):
    return weighted_search(game_map, start_state, state_key=state_key,
                           is_goal=is_goal, successors=successors, runtime=runtime,
                           heuristic=lambda m, s: 0 if is_goal(m, s) else 1)
