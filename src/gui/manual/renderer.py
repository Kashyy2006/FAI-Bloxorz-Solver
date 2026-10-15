import math

import pygame

from .settings import (
    TILE_WIDTH,
    TILE_DEPTH,
    TILE_HEIGHT,
    FLOOR_COLOR,
    GOAL_COLOR,
    FRAGILE_COLOR,
    BLOCK_COLOR
)

def darker(color, factor):
    return tuple(int(value * factor) for value in color)


def draw_cube(screen, row, col, camera, color, depth,
              elevation=0):

    # Tọa độ 4 góc của ô trên bản đồ
    corners = [
        (row - 0.5, col - 0.5),
        (row - 0.5, col + 0.5),
        (row + 0.5, col + 0.5),
        (row + 0.5, col - 0.5)
    ]

    top = []

    for r, c in corners:
        x, y = camera.project(r, c)
        top.append((x, y - camera.scale(elevation)))

    # Vẽ các mặt bên hướng về phía người xem
    # dựa trên cạnh nào nằm phía trước.
    _, center_y = camera.project(row, col)
    scaled_elevation = camera.scale(elevation)

    for i in range(4):
        p1 = top[i]
        p2 = top[(i + 1) % 4]

        midpoint_y = (p1[1] + p2[1]) / 2

        if midpoint_y < center_y - scaled_elevation:
            continue

        side = [
            p1,
            p2,
            (p2[0], p2[1] + camera.scale(depth)),
            (p1[0], p1[1] + camera.scale(depth))
        ]

        shade = 0.55 if i % 2 == 0 else 0.75

        pygame.draw.polygon(
            screen, darker(color, shade), side
        )

    pygame.draw.polygon(screen, color, top)
    pygame.draw.polygon(
        screen, (35, 45, 60), top, max(1, round(camera.scale(2)))
    )

def draw_map(screen, grid, camera):
    tile_colors = {
        "floor": FLOOR_COLOR,
        "goal": GOAL_COLOR,
        "fragile": FRAGILE_COLOR,
        "soft": (130, 210, 230),
        "heavy": (190, 145, 225),
        "split": (235, 205, 105),
        "bridge": (115, 190, 175),
    }
    tiles = []

    for row in range(len(grid)):
        for col in range(len(grid[row])):
            tile = grid[row][col]

            if tile == "void":
                continue

            x, y = camera.project(row, col)
            tiles.append((y, row, col, tile))

    tiles.sort(key=lambda item: item[0])

    for _, row, col, tile in tiles:
        color = tile_colors.get(tile, FLOOR_COLOR)

        draw_cube(
            screen, row, col,
            camera, color, TILE_DEPTH
        )

def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _draw_prism(screen, camera, center, long_axis, color, length=2.0):
    """Draw the block as one oriented 3D prism in row/column/height space."""
    long_len = length / 2
    perp = (-long_axis[1], long_axis[0], 0.0)
    # Keep a stable horizontal cross axis when the long axis is vertical.
    if abs(perp[0]) + abs(perp[1]) < 1e-6:
        perp = (0.0, 1.0, 0.0)
    third = _cross(long_axis, perp)
    vectors = (long_axis, perp, third)
    half_sizes = (long_len, 0.5, 0.5)
    vertices = {}
    for a in (-1, 1):
        for b in (-1, 1):
            for c in (-1, 1):
                point = [center[i] + a * vectors[0][i] * half_sizes[0]
                         + b * vectors[1][i] * half_sizes[1]
                         + c * vectors[2][i] * half_sizes[2]
                         for i in range(3)]
                x, y = camera.project(point[0], point[1])
                vertices[(a, b, c)] = (x, y - camera.scale(point[2] * 40))

    faces = [
        ([(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)], 0.62),
        ([(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], 0.72),
        ([(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], 0.82),
        ([(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)], 0.58),
        ([(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], 1.0),
        ([(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)], 0.42),
    ]
    polygons = [(sum(p[1] for p in (vertices[v] for v in face)) / 4,
                 [vertices[v] for v in face], shade)
                for face, shade in faces]
    for _, points, shade in sorted(polygons, key=lambda item: item[0]):
        pygame.draw.polygon(screen, darker(color, shade), points)
        pygame.draw.polygon(screen, (35, 45, 60), points,
                            max(1, round(camera.scale(1.5))))


def _state_center(state):
    cells = state["cells"]
    return (sum(cell[0] for cell in cells) / len(cells),
            sum(cell[1] for cell in cells) / len(cells))


def _axis_for_mode(mode):
    if mode == "HORIZONTAL":
        return (0.0, 1.0, 0.0)
    if mode == "VERTICAL":
        return (1.0, 0.0, 0.0)
    return (0.0, 0.0, 1.0)


def draw_block(screen, state, camera):
    mode = state["mode"]
    cells = state["cells"]
    if mode == "SPLIT":
        for index, (row, col) in enumerate(cells):
            _draw_prism(screen, camera, (row, col, 0.5), (0, 0, 1),
                        (80, 170, 255), length=1.0)
            if index == state["active"]:
                x, y = camera.project(row, col)
                pygame.draw.circle(screen, (255, 255, 255),
                                   (int(x), int(y - camera.scale(40))),
                                   max(3, round(camera.scale(8))),
                                   max(1, round(camera.scale(2))))
        return

    row, col = _state_center(state)
    z = 1.0 if mode == "UPRIGHT" else 0.5
    _draw_prism(screen, camera, (row, col, z), _axis_for_mode(mode), BLOCK_COLOR)


def draw_animated_block(screen, start_state, end_state, action, progress, camera):
    """Rotate the cuboid over its edge while its center follows the roll arc."""
    t = progress * progress * (3 - 2 * progress)
    start_row, start_col = _state_center(start_state)
    end_row, end_col = _state_center(end_state)
    row = start_row + (end_row - start_row) * t
    col = start_col + (end_col - start_col) * t
    start_mode, end_mode = start_state["mode"], end_state["mode"]

    if start_mode == "UPRIGHT" and end_mode != "UPRIGHT":
        direction = {"UP": (-1, 0, 0), "DOWN": (1, 0, 0),
                     "LEFT": (0, -1, 0), "RIGHT": (0, 1, 0)}[action]
        angle = t * math.pi / 2
        axis = (direction[0] * math.sin(angle),
                direction[1] * math.sin(angle), math.cos(angle))
        z = 0.5 + 0.5 * math.cos(angle)
    elif start_mode != "UPRIGHT" and end_mode == "UPRIGHT":
        old_axis = _axis_for_mode(start_mode)
        angle = t * math.pi / 2
        axis = (old_axis[0] * math.cos(angle),
                old_axis[1] * math.cos(angle), math.sin(angle))
        z = 0.5 + 0.5 * math.sin(angle)
    else:
        axis = _axis_for_mode(start_mode)
        z = 0.5

    _draw_prism(screen, camera, (row, col, z), axis, BLOCK_COLOR)
