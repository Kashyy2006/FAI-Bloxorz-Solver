"""Stable wire identifiers shared by engine, solver, GUI and benchmarks."""
from src.engine.models import Action
ALGORITHMS = ("BFS", "DFS", "UCS", "ASTAR")
ACTIONS = frozenset(action.value for action in Action)
STATUSES = frozenset(("SOLVED", "UNSOLVABLE", "TIMEOUT", "CANCELLED", "ERROR"))
COST_MODEL = "base1_fragile2_switch1_v1"
GOAL_INDICATOR = "goal_indicator_v1"
REVERSE_BFS = "reverse_bfs_manhattan_fallback_v1"
MANHATTAN = "manhattan_orientation_v1"
HEURISTICS = frozenset((GOAL_INDICATOR, REVERSE_BFS, MANHATTAN))
