"""TV5 compatibility entry point; engine owns all cost rules."""
from src.engine import rules


def calculate_step_cost(game_map, current_state, next_state, action: str) -> int:
    return rules.step_cost(game_map, current_state, action, next_state)
