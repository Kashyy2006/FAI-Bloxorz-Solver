def calculate_step_cost(game_map, current_state, next_state, action: str) -> int:
    if action == "SWITCH":
        return 1
    current_cells = set(current_state.cells)
    next_cells = set(next_state.cells)
    new_cells = next_cells - current_cells
    fragile_tiles = getattr(game_map, "fragile_tiles", set())
    F = sum(1 for cell in new_cells if cell in fragile_tiles)
    soft_switches = getattr(game_map, "soft_switches", set())
    heavy_switches = getattr(game_map, "heavy_switches", set())
    T = 0
    for cell in new_cells:
        if cell in soft_switches:
            T += 1
        elif cell in heavy_switches and next_state.mode == "UPRIGHT":
            T += 1
    return 1 + 2 * F + T
