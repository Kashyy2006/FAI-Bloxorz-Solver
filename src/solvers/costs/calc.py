from src.engine.models import Mode


def calculate_step_cost(game_map, current_state, next_state, action: str) -> int:
    if action == "SWITCH":
        return 1

    new_cells = set(next_state.cells) - set(current_state.cells)
    fragile_count = 0
    triggered_switches = 0
    for cell in new_cells:
        tile = game_map.tile_at(cell)
        fragile_count += tile == "fragile"
        triggered_switches += (
            tile == "soft"
            or (tile == "heavy" and next_state.mode in (Mode.UPRIGHT, "UPRIGHT"))
        )
    return 1 + 2 * fragile_count + triggered_switches
