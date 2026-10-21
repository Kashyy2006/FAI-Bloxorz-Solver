"""Tile labels and picking use the same projected top faces as the renderer."""
import pygame

TILE_NAMES = {"floor": "Floor", "goal": "Goal", "fragile": "Fragile",
              "soft": "Soft switch", "heavy": "Heavy switch",
              "split": "Split switch", "bridge": "Bridge"}
TILE_MARKS = {"goal": "GOAL", "fragile": "FRAGILE", "soft": "SOFT",
              "heavy": "HEAVY", "split": "SPLIT", "bridge": "BRIDGE"}


def tile_polygon(camera, cell, level=1.0):
    row, col = cell
    # Closed bridges remain hoverable at board height.
    elevation = -70 * (1 - level) if level > 0.001 else 0
    return [(x, y - camera.scale(elevation)) for x, y in
            (camera.project(row+dr, col+dc) for dr, dc in
             ((-.5, -.5), (-.5, .5), (.5, .5), (.5, -.5)))]


def _contains(point, polygon):
    x, y = point
    crosses = [(b[0]-a[0])*(y-a[1]) - (b[1]-a[1])*(x-a[0])
               for a, b in zip(polygon, polygon[1:] + polygon[:1])]
    return all(v >= -0.01 for v in crosses) or all(v <= 0.01 for v in crosses)


def hovered_tile(game_map, camera, mouse, bridge_levels=None, hidden_cells=()):
    candidates = []
    for row, tiles in enumerate(game_map.grid):
        for col, tile in enumerate(tiles):
            cell = row, col
            if tile == "void" or cell in hidden_cells:
                continue
            level = (bridge_levels or {}).get(cell, 1.0) if tile == "bridge" else 1.0
            polygon = tile_polygon(camera, cell, level)
            if _contains(mouse, polygon):
                candidates.append((sum(y for _, y in polygon), cell))
    return max(candidates)[1] if candidates else None


def tile_description(game_map, state, cell):
    tile = game_map.tile_at(cell)
    return f"{TILE_NAMES.get(tile, tile)} [{cell[0]}, {cell[1]}]"


def draw_tile_labels(screen, game_map, camera, bridge_levels=None, hidden_cells=()):
    font = pygame.font.Font(None, max(9, round(camera.scale(17))))
    for row, tiles in enumerate(game_map.grid):
        for col, tile in enumerate(tiles):
            cell = row, col
            if tile not in TILE_MARKS or cell in hidden_cells:
                continue
            level = (bridge_levels or {}).get(cell, 1.0) if tile == "bridge" else 1.0
            if tile == "bridge" and level <= .001:
                continue
            polygon = tile_polygon(camera, cell, level)
            center = (sum(x for x, _ in polygon)/4, sum(y for _, y in polygon)/4)
            label = font.render(TILE_MARKS[tile], True, (245, 250, 255))
            max_width = max(8, round(max(x for x, _ in polygon)-min(x for x, _ in polygon))-8)
            if label.get_width() > max_width:
                ratio = max_width/label.get_width()
                label = pygame.transform.smoothscale(label, (max_width, max(5, round(label.get_height()*ratio))))
            label.set_alpha(100)
            screen.blit(label, label.get_rect(center=center))


def draw_tile_tooltip(screen, font, game_map, state, camera, mouse,
                      bridge_levels=None, hidden_cells=()):
    cell = hovered_tile(game_map, camera, mouse, bridge_levels, hidden_cells)
    if cell is None:
        return
    tile = game_map.tile_at(cell)
    level = (bridge_levels or {}).get(cell, 1.0) if tile == "bridge" else 1.0
    pygame.draw.polygon(screen, (240, 225, 145), tile_polygon(camera, cell, level), 2)
    # Keep the tooltip inside the window.
    from .text_panel import wrapped_lines
    lines = wrapped_lines(font, tile_description(game_map, state, cell), min(500, screen.get_width()-32))
    labels = [font.render(line, True, (245, 245, 250)) for line in lines]
    width = max(label.get_width() for label in labels)+20
    height = len(labels)*font.get_linesize()+14
    rect = pygame.Rect(mouse[0]+16, mouse[1]+18, width, height).clamp(screen.get_rect())
    pygame.draw.rect(screen, (15, 22, 35), rect, border_radius=6)
    pygame.draw.rect(screen, (105, 125, 155), rect, 1, border_radius=6)
    for i, label in enumerate(labels):
        screen.blit(label, (rect.x+10, rect.y+7+i*font.get_linesize()))
