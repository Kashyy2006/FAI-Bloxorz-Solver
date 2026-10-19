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

def draw_map(screen, grid, camera, hidden_cells=()):
    # Vẽ các ô hợp lệ của bản đồ theo thứ tự chiều sâu.
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

            if tile == "void" or (row, col) in hidden_cells:
                continue

            # Lưu y để sắp các ô từ phía sau ra phía trước khi vẽ chồng.
            x, y = camera.project(row, col)
            tiles.append((y, row, col, tile))

    tiles.sort(key=lambda item: item[0])

    for _, row, col, tile in tiles:
        color = tile_colors.get(tile, FLOOR_COLOR)

        draw_cube(
            screen, row, col,
            camera, color, TILE_DEPTH
        )


def draw_front_tiles(screen, grid, camera, depth_y, hidden_cells=()):
    # Vẽ lại các ô ở phía trước khối để tạo hiện tượng che khuất theo chiều sâu.
    tile_colors = {
        "floor": FLOOR_COLOR,
        "goal": GOAL_COLOR,
        "fragile": FRAGILE_COLOR,
        "soft": (130, 210, 230),
        "heavy": (190, 145, 225),
        "split": (235, 205, 105),
        "bridge": (115, 190, 175),
    }
    front_tiles = []
    for row, cells in enumerate(grid):
        for col, tile in enumerate(cells):
            if tile == "void" or (row, col) in hidden_cells:
                continue
            _, tile_y = camera.project(row, col)
            if tile_y > depth_y:
                front_tiles.append((tile_y, row, col, tile))

    for _, row, col, tile in sorted(front_tiles):
        draw_cube(screen, row, col, camera,
                  tile_colors.get(tile, FLOOR_COLOR), TILE_DEPTH)

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
    # Sắp mặt theo độ cao trung bình để mặt ở xa được vẽ trước.
    polygons = [(sum(p[1] for p in (vertices[v] for v in face)) / 4,
                 [vertices[v] for v in face], shade)
                for face, shade in faces]
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
    z = (1.0 if mode == "UPRIGHT" else 0.5) + height_offset
    _draw_prism(screen, camera, (row, col, z), _axis_for_mode(mode), BLOCK_COLOR)


def draw_animated_block(screen, start_state, end_state, action, progress, camera):
    # Vẽ hoạt ảnh khối lăn giữa trạng thái đầu và trạng thái cuối.
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
