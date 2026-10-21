import math
from src.engine.geometry import movement_pose
from src.engine.models import State, Action

import pygame
from .animations import MOVE_DURATION, SPLIT_DURATION

from .settings import (
    TILE_WIDTH,
    TILE_DEPTH,
    TILE_HEIGHT,
    FLOOR_COLOR,
    GOAL_COLOR,
    FRAGILE_COLOR,
    BLOCK_COLOR
)

TILE_COLORS = {
        "floor": FLOOR_COLOR,
        "goal": GOAL_COLOR,
        "fragile": FRAGILE_COLOR,
        "soft": (130, 210, 230),
        "heavy": (190, 145, 225),
        "split": (235, 205, 105),
        "bridge": (115, 190, 175),
    }


def darker(color, factor):
    # Làm tối màu.
    return tuple(int(value * factor) for value in color)


def draw_cube(screen, row, col, camera, color, depth,
              elevation=0):
    # Vẽ một khối lập phương tại ô bản đồ với các mặt có đổ bóng.

    # Tạo bốn góc của mặt trên quanh tâm ô; mỗi cạnh dài một ô.
    corners = [
        (row - 0.5, col - 0.5),
        (row - 0.5, col + 0.5),
        (row + 0.5, col + 0.5),
        (row + 0.5, col - 0.5)
    ]

    top = []

    for r, c in corners:
        x, y = camera.project(r, c)
        # Nâng mặt trên lên theo elevation (đơn vị pixel sau khi scale).
        top.append((x, y - camera.scale(elevation)))

    # So độ cao cạnh với tâm ô để chỉ vẽ các mặt bên hướng về người xem.
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

def draw_map(screen, grid, camera, hidden_cells=(), bridge_levels=None):
    # Vẽ các ô hợp lệ của bản đồ theo thứ tự chiều sâu.

    tiles = []

    for row in range(len(grid)):
        for col in range(len(grid[row])):
            tile = grid[row][col]

            if tile == "void" or (row, col) in hidden_cells:
                continue

            # Lưu y để sắp các ô từ phía sau ra phía trước khi vẽ chồng.
            x, y = camera.project(row, col)
            tiles.append((y, row, col, tile))

    tiles.sort(key=lambda item: item[0])

    for _, row, col, tile in tiles:
        color = TILE_COLORS.get(tile, FLOOR_COLOR)

        _draw_tile(screen, row, col, tile, camera, color, bridge_levels)


def draw_front_tiles(screen, grid, camera, depth_y, hidden_cells=(), bridge_levels=None):
    # Vẽ lại các ô ở phía trước khối để tạo hiện tượng che khuất theo chiều sâu.

    front_tiles = []
    for row, cells in enumerate(grid):
        for col, tile in enumerate(cells):
            if tile == "void" or (row, col) in hidden_cells:
                continue
            _, tile_y = camera.project(row, col)
            if tile_y > depth_y:
                front_tiles.append((tile_y, row, col, tile))

    for _, row, col, tile in sorted(front_tiles):
        _draw_tile(screen, row, col, tile, camera,
                   TILE_COLORS.get(tile, FLOOR_COLOR), bridge_levels)

def _draw_tile(screen, row, col, tile, camera, color, bridge_levels):
    level = (bridge_levels or {}).get((row, col), 1.0) if tile == "bridge" else 1.0
    if level <= 0.001:
        return
    elevation = -70 * (1 - level)
    if tile == "bridge":
        color = darker(color, 0.5 + 0.5 * level)
    draw_cube(screen, row, col, camera, color, TILE_DEPTH, elevation=elevation)


def _cross(a, b):
    # Tính tích có hướng của hai vector ba chiều.
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _rotate_vector(vector, axis, angle):
    # Xoay vector quanh trục bằng công thức Rodrigues.
    cross = _cross(axis, vector)
    dot = sum(axis[i] * vector[i] for i in range(3))
    cosine, sine = math.cos(angle), math.sin(angle)
    return tuple(vector[i] * cosine + cross[i] * sine
                 + axis[i] * dot * (1 - cosine) for i in range(3))


def _draw_prism(screen, camera, center, long_axis, color, length=2.0):
    # Vẽ khối dưới dạng lăng trụ 3D theo trục và vị trí cho trước.
    long_len = length / 2
    # Dựng ba trục vuông góc: trục dài, trục ngang còn lại và trục đứng.
    perp = (-long_axis[1], long_axis[0], 0.0)
    if abs(perp[0]) + abs(perp[1]) < 1e-6:
        perp = (0.0, 1.0, 0.0)
    norm = math.sqrt(sum(value * value for value in perp))
    perp = tuple(value / norm for value in perp)
    third = _cross(long_axis, perp)
    vectors = (long_axis, perp, third)
    half_sizes = (long_len, 0.5, 0.5)
    vertices = {}
    # Tổ hợp +/- trên ba trục tạo tám đỉnh quanh tâm khối.
    for a in (-1, 1):
        for b in (-1, 1):
            for c in (-1, 1):
                point = [center[i] + a * vectors[0][i] * half_sizes[0]
                         + b * vectors[1][i] * half_sizes[1]
                         + c * vectors[2][i] * half_sizes[2]
                         for i in range(3)]
                x, y = camera.project(point[0], point[1])
                vertices[(a, b, c)] = (x, y - camera.scale(point[2] * 40))

    # Mỗi mặt lưu bốn đỉnh và độ sáng riêng để tạo khối có chiều sâu.
    faces = [
        ([(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)], 0.62),
        ([(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], 0.72),
        ([(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], 0.82),
        ([(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)], 0.58),
        ([(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], 1.0),
        ([(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)], 0.42),
    ]
    # Suy ra hướng nhìn 3D từ phép chiếu thực tế của camera (kể cả khi xoay).
    # Không vẽ mặt quay lưng: viền mặt sau chính là các cạnh "xuyên thấu".
    origin = camera.project(0, 0)
    row_projection = camera.project(1, 0)
    col_projection = camera.project(0, 1)
    rx, ry = (row_projection[i] - origin[i] for i in range(2))
    cx, cy = (col_projection[i] - origin[i] for i in range(2))
    vertical_scale = camera.scale(40)
    view = (vertical_scale * cx, -vertical_scale * rx, cx * ry - rx * cy)
    polygons = []
    for face, shade in faces:
        local_center = [sum(vertex[i] for vertex in face) / 4 for i in range(3)]
        normal = [sum(local_center[j] * vectors[j][i] for j in range(3))
                  for i in range(3)]
        if sum(normal[i] * view[i] for i in range(3)) <= 1e-8:
            continue
        face_center = [center[i] + sum(local_center[j] * half_sizes[j] * vectors[j][i]
                                      for j in range(3)) for i in range(3)]
        depth = sum(face_center[i] * view[i] for i in range(3))
        polygons.append((depth, [vertices[v] for v in face], shade))
    for _, points, shade in sorted(polygons, key=lambda item: item[0]):
        pygame.draw.polygon(screen, darker(color, shade), points)
        pygame.draw.polygon(screen, (35, 45, 60), points,
                            max(1, round(camera.scale(1.5))))


def _state_center(state):
    # Tính tâm khối từ danh sách các ô đang chiếm.
    cells = state["cells"]
    return (sum(cell[0] for cell in cells) / len(cells),
            sum(cell[1] for cell in cells) / len(cells))


def _axis_for_mode(mode):
    # Lấy vector trục dài tương ứng với tư thế của khối.
    if mode == "HORIZONTAL":
        return (0.0, 1.0, 0.0)
    if mode == "VERTICAL":
        return (1.0, 0.0, 0.0)
    return (0.0, 0.0, 1.0)


def draw_block(screen, state, camera, height_offset=0.0):
    # Vẽ khối ở tư thế hiện tại, gồm cả trạng thái tách đôi.
    mode = state["mode"]
    cells = state["cells"]
    if mode == "SPLIT":
        for index, (row, col) in sorted(enumerate(cells),
                                        key=lambda item: camera.project(*item[1])[1]):
            _draw_unit_cube(screen, camera, (row, col, 0.5), index == state["active"])
        return

    row, col = _state_center(state)
    z = (1.0 if mode == "UPRIGHT" else 0.5) + height_offset
    _draw_prism(screen, camera, (row, col, z), _axis_for_mode(mode), BLOCK_COLOR)


def _draw_unit_cube(screen, camera, center, active=False, alpha=1.0, axis=(0,0,1)):
    if alpha <= 0:
        return
    target = screen if alpha >= 1 else pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    _draw_prism(target, camera, center, axis, (80,170,255), length=1)
    if active:
        x, y = camera.project(center[0], center[1])
        pygame.draw.circle(target, (240,250,255),
                           (round(x), round(y-camera.scale((center[2]+0.5)*40))),
                           max(3,round(camera.scale(8))),max(1,round(camera.scale(2))))
    if target is not screen:
        target.set_alpha(round(255*alpha))
        screen.blit(target,(0,0))


def _draw_split_transition(screen, start, end, action, progress, camera):
    # Roll onto the switch first, then separate and arc to the engine destinations.
    mode, cells, active = movement_pose(State(start["mode"], start["cells"], start.get("active")), Action(action))
    origin = cells[0]
    arrived = {"mode": mode.value, "cells": list(cells), "active": active}
    roll_fraction = MOVE_DURATION / SPLIT_DURATION
    if progress < roll_fraction:
        draw_animated_block(screen, start, arrived, action, progress/roll_fraction, camera)
        return
    q = min(1.0,(progress-roll_fraction)/(1-roll_fraction))
    eased = q*q*(3-2*q)
    x,y = camera.project(*origin)
    if q < 0.9:
        radius = max(2,round(camera.scale(12+36*q)))
        pygame.draw.ellipse(screen,(85,210,250),
                            (round(x-radius),round(y-radius/2),radius*2,max(2,radius)),
                            max(1,round(camera.scale(2))))
    cubes = []
    for index, (dr,dc) in enumerate(end["cells"]):
        row = origin[0]+(dr-origin[0])*eased
        col = origin[1]+(dc-origin[1])*eased
        z = (0.5+index)*(1-eased)+0.5*eased+math.sin(q*math.pi)*0.8
        cubes.append((index,(row,col,z)))
    for index, center in sorted(cubes,key=lambda item:camera.project(*item[1][:2])[1]):
        _draw_unit_cube(screen,camera,center,index == end["active"])


def _draw_cube_move(screen,start,end,progress,camera):
    t=progress*progress*(3-2*progress)
    fixed=tuple(start["cells"][1-start["active"]])
    before=start["cells"][start["active"]]
    target=next(tuple(c) for c in end["cells"] if tuple(c) != fixed)
    moving=(before[0]+(target[0]-before[0])*t,before[1]+(target[1]-before[1])*t,0.5)
    if end["mode"] != "SPLIT" and progress > 0.85:
        draw_block(screen,end,camera)
        return
    for center,active in sorted([((*fixed,0.5),False),(moving,True)],
                                 key=lambda item:camera.project(*item[0][:2])[1]):
        _draw_unit_cube(screen,camera,center,active)


def draw_animated_block(screen, start_state, end_state, action, progress, camera):
    # Vẽ hoạt ảnh khối lăn giữa trạng thái đầu và trạng thái cuối.
    if action == "SWITCH":
        draw_block(screen, end_state, camera)
        return
    if start_state["mode"] != "SPLIT" and end_state["mode"] == "SPLIT":
        _draw_split_transition(screen,start_state,end_state,action,progress,camera)
        return
    if start_state["mode"] == "SPLIT":
        _draw_cube_move(screen,start_state,end_state,progress,camera)
        return
    # Làm mượt tiến độ để khối bắt đầu và kết thúc chuyển động êm.
    t = progress * progress * (3 - 2 * progress)
    start_row, start_col = _state_center(start_state)
    end_row, end_col = _state_center(end_state)
    start_mode, end_mode = start_state["mode"], end_state["mode"]

    if start_mode == "UPRIGHT" and end_mode != "UPRIGHT":
        # Giữ cạnh đáy làm trục xoay; tâm khối đi theo cung tròn khi khối ngã.
        dr, dc = {"UP": (-1, 0), "DOWN": (1, 0),
                  "LEFT": (0, -1), "RIGHT": (0, 1)}[action]
        roll_axis = (-dc, dr, 0)
        pivot = (start_row + dr * 0.5, start_col + dc * 0.5, 0.0)
        angle = t * math.pi / 2
        offset = (start_row - pivot[0], start_col - pivot[1], 1.0)
        rotated = _rotate_vector(offset, roll_axis, angle)
        row, col, z = (pivot[i] + rotated[i] for i in range(3))
        axis = _rotate_vector((0.0, 0.0, 1.0), roll_axis, angle)
    elif start_mode != "UPRIGHT" and end_mode == "UPRIGHT":
        # Dùng cạnh đầu của khối nằm làm trục xoay khi khối dựng lên.
        dr, dc = {"UP": (-1, 0), "DOWN": (1, 0),
                  "LEFT": (0, -1), "RIGHT": (0, 1)}[action]
        roll_axis = (-dc, dr, 0)
        pivot = (end_row - dr * 0.5, end_col - dc * 0.5, 0.0)
        angle = t * math.pi / 2
        offset = (start_row - pivot[0], start_col - pivot[1], 0.5)
        rotated = _rotate_vector(offset, roll_axis, angle)
        row, col, z = (pivot[i] + rotated[i] for i in range(3))
        axis = _rotate_vector(_axis_for_mode(start_mode), roll_axis, angle)
    else:
        # Nếu tư thế không đổi, khối trượt thẳng trên sàn và giữ nguyên trục.
        row = start_row + (end_row - start_row) * t
        col = start_col + (end_col - start_col) * t
        z = 0.5
        axis = _axis_for_mode(start_mode)

    _draw_prism(screen, camera, (row, col, z), axis, BLOCK_COLOR)


def draw_falling_block(screen, state, camera, progress, action, supported_cells=()):
    """Tip a half-supported block towards the missing tile, then fall and fade."""
    t = max(0.0, min(1.0, progress))
    cells = [tuple(c) for c in state["cells"]]
    if state["mode"] == "SPLIT":
        dr,dc = {"UP":(-1,0),"DOWN":(1,0),"LEFT":(0,-1),"RIGHT":(0,1)}.get(action,(0,0))
        for index,cell in sorted(enumerate(cells),key=lambda item:camera.project(*item[1])[1]):
            if cell in supported_cells:
                _draw_unit_cube(screen,camera,(*cell,0.5),index == state["active"])
            elif t < 1:
                center=(cell[0]+dr*0.3*t*t,cell[1]+dc*0.3*t*t,0.5-6*t*t)
                axis=_rotate_vector((0,0,1),(-dc,dr,0),t*0.5) if dr or dc else (0,0,1)
                alpha=min(1.0,(1-t)/0.45)
                _draw_unit_cube(screen,camera,center,False,alpha,axis)
        return
    if t >= 1:
        return
    row, col = _state_center(state)
    z = 1.0 if state["mode"] == "UPRIGHT" else 0.5
    axis = _axis_for_mode(state["mode"])
    dr, dc = {"UP": (-1,0), "DOWN": (1,0), "LEFT": (0,-1), "RIGHT": (0,1)}.get(action, (0,0))
    supported = [c for c in cells if c in supported_cells]
    if len(cells) == 2 and len(supported) == 1:
        support = supported[0]
        missing = next(c for c in cells if c not in supported)
        dr, dc = missing[0] - support[0], missing[1] - support[1]
        pivot = (support[0] + dr * 0.5, support[1] + dc * 0.5, 0)
        angle = min(1.0, t / 0.55) * math.pi * 0.42
        rotation_axis = (-dc, dr, 0)
        offset = _rotate_vector((row-pivot[0], col-pivot[1], z), rotation_axis, angle)
        row, col, z = (pivot[i]+offset[i] for i in range(3))
        axis = _rotate_vector(axis, rotation_axis, angle)
    row += dr * 0.3 * t*t
    col += dc * 0.3 * t*t
    z -= 6 * t*t
    target = screen
    if t > 0.55:
        target = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    _draw_prism(target, camera, (row,col,z), axis, BLOCK_COLOR)
    if target is not screen:
        target.set_alpha(round(255 * (1-t)/0.45))
        screen.blit(target, (0,0))
