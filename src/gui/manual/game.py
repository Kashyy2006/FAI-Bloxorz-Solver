# Giao diện Pygame để chơi thủ công, chọn màn và chỉnh cài đặt.

import sys
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    __package__ = "src.gui.manual"

import pygame
from src.engine import Mode, State, Status, initial_state, load_map, transition

from .camera import Camera
from .renderer import draw_animated_block, draw_block, draw_front_tiles, draw_map
from .settings import BACKGROUND_COLOR, FPS, HEIGHT, WIDTH
from ..solver.controller import SolverController

ROOT = Path(__file__).resolve().parents[3]
MAPS_DIR = ROOT / "data" / "maps"
BGM_DIR = ROOT / "data" / "bgm"


# Nạp các bản đồ hợp lệ bằng validator dùng chung của engine.
def _load_maps():
    maps = []
    for path in sorted(MAPS_DIR.glob("*.json")):
        try:
            maps.append((path, load_map(path)))
        except (OSError, ValueError) as error:
            print(f"Could not load map {path.name}: {error}")
    return maps



# Chuyển State của engine sang dạng dict mà solver và renderer hiện dùng.
def _state_as_dict(state):
    return {"mode": state.mode.value, "cells": list(state.cells),
            "active": state.active, "bridges": {}}


# Tạo callback tương thích với solver nhưng dùng engine cho luật di chuyển.
def _solver_move_for(game_map):
    def move(state_data, action, _grid):
        state = State(Mode(state_data["mode"]),
                      tuple(tuple(cell) for cell in state_data["cells"]),
                      state_data.get("active"))
        result = transition(game_map, state, action)
        if result.status not in (Status.OK, Status.WON):
            return None
        return _state_as_dict(result.next_state)

    return move


# Chuyển map engine sang dạng dict cần bởi giao diện solver hiện tại.
def _map_as_dict(game_map):
    return {"id": game_map.id, "name": game_map.name,
            "grid": [list(row) for row in game_map.grid], "bridges": []}


# Khôi phục State bất biến từ snapshot dictionary của solver.
def _state_from_dict(state_data):
    return State(Mode(state_data["mode"]),
                 tuple(tuple(cell) for cell in state_data["cells"]),
                 state_data.get("active"))


# Tạo tư thế đích chỉ để diễn hoạt ảnh của nước đi engine báo thua.
def _failed_move_preview(state, action):
    # Tính tư thế hình học sau cú lăn để minh họa; engine vẫn quyết định nước đi thua.
    mode = state.mode.value
    cells = state.cells
    row, col = cells[0]
    dr, dc = {"UP": (-1, 0), "DOWN": (1, 0),
              "LEFT": (0, -1), "RIGHT": (0, 1)}[action]

    if mode == "UPRIGHT":
        # Khối đứng sẽ nằm chiếm hai ô theo hướng lăn.
        if action == "UP":
            next_mode, next_cells = Mode.VERTICAL, ((row - 2, col), (row - 1, col))
        elif action == "DOWN":
            next_mode, next_cells = Mode.VERTICAL, ((row + 1, col), (row + 2, col))
        elif action == "LEFT":
            next_mode, next_cells = Mode.HORIZONTAL, ((row, col - 2), (row, col - 1))
        else:
            next_mode, next_cells = Mode.HORIZONTAL, ((row, col + 1), (row, col + 2))
    elif mode == "HORIZONTAL":
        # Khối ngang đứng lên khi lăn dọc trục dài, còn lại tịnh tiến một hàng.
        if action == "LEFT":
            next_mode, next_cells = Mode.UPRIGHT, ((row, col - 1),)
        elif action == "RIGHT":
            next_mode, next_cells = Mode.UPRIGHT, ((row, col + 2),)
        else:
            next_mode = Mode.HORIZONTAL
            next_cells = tuple((r + dr, c + dc) for r, c in cells)
    else:  # VERTICAL
        # Khối dọc đứng lên khi lăn dọc trục dài, còn lại tịnh tiến một cột.
        if action == "UP":
            next_mode, next_cells = Mode.UPRIGHT, ((row - 1, col),)
        elif action == "DOWN":
            next_mode, next_cells = Mode.UPRIGHT, ((row + 2, col),)
        else:
            next_mode = Mode.VERTICAL
            next_cells = tuple((r + dr, c + dc) for r, c in cells)

    return State(next_mode, next_cells)


# Đổi hướng phím theo góc camera để phím luôn đi theo góc nhìn.
def _action_from_view(action, camera_angle):
    quarter_turns = round(camera_angle / 90) % 4
    rotated_actions = {
        "UP": "LEFT", "LEFT": "DOWN",
        "DOWN": "RIGHT", "RIGHT": "UP",
    }
    for _ in range(quarter_turns):
        action = rotated_actions[action]
    return action


def _controls_hint(camera_angle):
    # Chỉ dẫn hướng đi theo góc nhìn camera
    view_keys = ("Lên", "Xuống", "Trái", "Phải")
    map_actions = ("UP", "DOWN", "LEFT", "RIGHT")
    return " | ".join(
        f"{key}={_action_from_view(action, camera_angle)}"
        for key, action in zip(view_keys, map_actions)
    )




# Vẽ một dòng chữ tại vị trí giữa được chỉ định.
def _text(screen, font, value, center, color=(240, 243, 250)):
    surface = font.render(str(value), True, color)
    screen.blit(surface, surface.get_rect(center=center))


# Vẽ nút và trả về box dùng để kiểm tra tương tác.
def _button(screen, font, label, rect, mouse_pos, color=(63, 83, 115)):
    box = pygame.Rect(rect)
    hovered = box.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (91, 123, 168) if hovered else color, box, border_radius=9)
    _text(screen, font, label, box.center)
    return box


# Khởi tạo và chạy vòng lặp giao diện chơi thủ công.
def main():
    pygame.init()
    try: # Lấy nhạc từ bgm
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        tracks = sorted(path for path in BGM_DIR.iterdir()
                        if path.is_file() and path.suffix.lower() in {".mp3", ".ogg", ".wav"})
        if tracks:
            pygame.mixer.music.load(str(tracks[0]))
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
            print(f"Playing background music: {tracks[0].name}")
    except (pygame.error, OSError) as error:
        print(f"Could not start background music from {BGM_DIR}: {error}")

    # Tạo cửa sổ, bộ đếm FPS và các font dùng chung cho giao diện.
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Bloxorz")
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 58)
    font = pygame.font.Font(None, 34)
    small_font = pygame.font.Font(None, 25)

    # Nạp map và nối solver với engine qua callback tương thích dữ liệu.
    maps = _load_maps()
    if not maps:
        print(f"No playable map JSON files found in {MAPS_DIR}")
    active_map = [None]

    def solver_move(state_data, action, grid):
        return _solver_move_for(active_map[0])(state_data, action, grid)

    solver = SolverController(move_fn=solver_move)

    # Trạng thái giao diện và ván chơi hiện tại.
    page = "menu"
    selected_map = 0
    state = None
    fallen_preview = None
    falling = None
    game_over_pending = False
    camera = None
    motion = None
    message = ""
    brightness = 0
    volume = 0.7
    fullscreen = False
    window_size = (WIDTH, HEIGHT)
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        mouse = pygame.mouse.get_pos()
        # Nhận thao tác bàn phím/chuột và cập nhật trang hoặc trạng thái ván.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                if camera:
                    camera.resize(event.w, event.h)
            elif event.type == pygame.MOUSEWHEEL and page == "game" and camera:
                camera.change_zoom(event.y)
            elif event.type == pygame.MOUSEMOTION and event.buttons[1] and page == "game" and camera:
                camera.move(*event.rel)
            elif event.type == pygame.MOUSEMOTION and event.buttons[0] and page == "settings":
                w, h = screen.get_size()
                if pygame.Rect(w // 2 - 150, h // 2 - 80, 300, 35).collidepoint(event.pos):
                    volume = max(0.0, min(1.0, (event.pos[0] - (w // 2 - 150)) / 300))
                    if pygame.mixer.get_init():
                        pygame.mixer.music.set_volume(volume)
                elif pygame.Rect(w // 2 - 150, h // 2 - 20, 300, 35).collidepoint(event.pos):
                    brightness = round(max(-100, min(100, (event.pos[0] - w // 2) * 2 / 3)))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if page == "game":
                        solver.reset()
                        page = "menu"
                    elif page != "menu":
                        page = "menu"
                    else:
                        running = False
                elif page == "game" and event.key == pygame.K_r and maps:
                    solver.reset()
                    state = initial_state(maps[selected_map][1])
                    fallen_preview = None
                    falling = None
                    game_over_pending = False
                    motion = None
                    message = ""
                elif page == "game" and event.key == pygame.K_l:
                    solver.reset()
                    page = "levels"
                elif page == "game" and event.key == pygame.K_q and camera:
                    camera.rotate(-1)
                elif page == "game" and event.key == pygame.K_e and camera:
                    camera.rotate(1)
                elif (page == "game" and maps and state and not game_over_pending
                      and solver.handle_key(event.key,
                                            _map_as_dict(maps[selected_map][1]),
                                            _state_as_dict(state),
                                            ready=motion is None)):
                    restore = solver.take_restore_state()
                    if restore is not None:
                        state, motion, message = _state_from_dict(restore), None, ""
                elif (page == "game" and state and not message
                      and not game_over_pending and not solver.busy):
                    view_action = {
                        pygame.K_UP: "UP", pygame.K_w: "UP",
                        pygame.K_DOWN: "DOWN", pygame.K_s: "DOWN",
                        pygame.K_LEFT: "LEFT", pygame.K_a: "LEFT",
                        pygame.K_RIGHT: "RIGHT", pygame.K_d: "RIGHT",
                    }.get(event.key)
                    if view_action and motion is None and camera and not camera.rotating:
                        action = _action_from_view(view_action, camera.angle)
                        solver.on_manual_move()
                        game_map = maps[selected_map][1]
                        result = transition(game_map, state, action)
                        if result.status is Status.LOST:
                            game_over_pending = True
                            motion = {"start": state,
                                      "end": _failed_move_preview(state, action),
                                      "action": action, "elapsed": 0.0,
                                      "status": result.status,
                                      "reason": result.reason}
                        elif result.status is Status.WON:
                            motion = {"start": state, "end": result.next_state,
                                      "action": action, "elapsed": 0.0,
                                      "status": result.status}
                        elif result.status is Status.OK:
                            motion = {"start": state, "end": result.next_state,
                                      "action": action, "elapsed": 0.0,
                                      "status": result.status}
                elif page == "levels" and maps:
                    if event.key in (pygame.K_UP, pygame.K_LEFT):
                        selected_map = (selected_map - 1) % len(maps)
                    elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                        selected_map = (selected_map + 1) % len(maps)
                    elif event.key == pygame.K_RETURN:
                        solver.reset()
                        game_map = maps[selected_map][1]
                        active_map[0] = game_map
                        state = initial_state(game_map)
                        fallen_preview = None
                        falling = None
                        game_over_pending = False
                        camera = Camera(game_map.cols, game_map.rows, *screen.get_size())
                        motion = None
                        message = ""
                        page = "game"

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                w, h = screen.get_size()
                if page == "menu":
                    if pygame.Rect(w // 2 - 120, h // 2 - 30, 240, 52).collidepoint(event.pos):
                        page = "levels"
                    elif pygame.Rect(w // 2 - 120, h // 2 + 38, 240, 52).collidepoint(event.pos):
                        page = "tutorial"
                    elif pygame.Rect(w // 2 - 120, h // 2 + 106, 240, 52).collidepoint(event.pos):
                        page = "settings"
                    elif pygame.Rect(w // 2 - 120, h // 2 + 174, 240, 52).collidepoint(event.pos):
                        running = False
                elif page == "settings":
                    if pygame.Rect(w // 2 - 150, h // 2 - 80, 300, 35).collidepoint(event.pos):
                        volume = max(0.0, min(1.0, (event.pos[0] - (w // 2 - 150)) / 300))
                        if pygame.mixer.get_init():
                            pygame.mixer.music.set_volume(volume)
                    elif pygame.Rect(w // 2 - 150, h // 2 - 20, 300, 35).collidepoint(event.pos):
                        brightness = round(max(-100, min(100, (event.pos[0] - (w // 2)) * 2 / 3)))
                    elif pygame.Rect(w // 2 - 150, h // 2 + 40, 300, 46).collidepoint(event.pos):
                        fullscreen = not fullscreen
                        if fullscreen:
                            window_size = screen.get_size()
                            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
                        if camera:
                            camera.resize(*screen.get_size())
                    elif pygame.Rect(w // 2 - 120, h // 2 + 125, 240, 48).collidepoint(event.pos):
                        page = "menu"
                elif page == "tutorial":
                    if pygame.Rect(w // 2 - 120, h - 75, 240, 48).collidepoint(event.pos):
                        page = "menu"
                elif page == "levels" and maps:
                    page_start = (selected_map // 7) * 7
                    page_count = min(7, len(maps) - page_start)
                    list_top = h // 2 - page_count * 24
                    for index in range(page_start, page_start + page_count):
                        rect = pygame.Rect(w // 2 - 250, list_top + (index - page_start) * 48, 500, 42)
                        if rect.collidepoint(event.pos):
                            solver.reset()
                            selected_map = index
                            game_map = maps[selected_map][1]
                            active_map[0] = game_map
                            state = initial_state(game_map)
                            fallen_preview = None
                            falling = None
                            game_over_pending = False
                            camera = Camera(game_map.cols, game_map.rows, *screen.get_size())
                            motion = None
                            message = ""
                            page = "game"
                            break
                    if pygame.Rect(w // 2 - 120, h - 75, 240, 48).collidepoint(event.pos):
                        page = "menu"
                elif page == "game":
                    if (maps and state and not game_over_pending
                            and solver.handle_click(event.pos, (w, h),
                                                    _map_as_dict(maps[selected_map][1]),
                                                    _state_as_dict(state),
                                                    ready=motion is None)):
                        restore = solver.take_restore_state()
                        if restore is not None:
                            state, motion, message = _state_from_dict(restore), None, ""
                            fallen_preview = None
                    elif pygame.Rect(12, 12, 150, 42).collidepoint(event.pos):
                        solver.reset()
                        page = "levels"
                    elif pygame.Rect(172, 12, 120, 42).collidepoint(event.pos):
                        solver.reset()
                        state = initial_state(maps[selected_map][1])
                        fallen_preview = None
                        falling = None
                        game_over_pending = False
                        motion = None
                        message = ""

        # Cập nhật camera, phát lại lời giải và hoàn tất hoạt ảnh di chuyển.
        if camera:
            camera.update(dt)
        if page == "game" and maps and state and camera:
            ready = (motion is None and not message and not game_over_pending
                     and not camera.rotating)
            action = solver.update(dt, ready)
            if action:
                result = transition(maps[selected_map][1], state, action)
                if result.status is Status.LOST:
                    game_over_pending = True
                    motion = {"start": state,
                              "end": _failed_move_preview(state, action),
                              "action": action, "elapsed": 0.0,
                              "status": result.status,
                              "reason": result.reason}
                elif result.status in (Status.OK, Status.WON):
                    motion = {"start": state, "end": result.next_state,
                              "action": action, "elapsed": 0.0,
                              "status": result.status}
                else:
                    message = f"Replay stopped: {result.reason or result.status.value}."
        if motion:
            motion["elapsed"] += dt
            if motion["elapsed"] >= 0.24:
                status = motion["status"]
                if status is Status.LOST:
                    if motion.get("reason") == "FRAGILE_UPRIGHT":
                        falling = {"state": motion["end"],
                                   "cell": motion["end"].cells[0],
                                   "elapsed": 0.0}
                    else:
                        fallen_preview = motion["end"]
                        message = "Game over! Press R to restart, L for levels."
                else:
                    state = motion["end"]
                motion = None
                if status is Status.WON:
                    message = "Level complete! Press L for levels."

        if falling:
            # Chờ hiệu ứng rơi kết thúc rồi mới thông báo game over.
            falling["elapsed"] += dt
            if falling["elapsed"] >= 0.55:
                message = "Game over! Press R to restart, L for levels."

        # Vẽ lại nội dung trang hiện tại, sau đó cập nhật cửa sổ.
        screen.fill(BACKGROUND_COLOR)
        w, h = screen.get_size()
        mouse = pygame.mouse.get_pos()
        if page == "menu":
            _text(screen, title_font, "BLOXORZ", (w // 2, h // 2 - 150))
            _button(screen, font, "Play", (w // 2 - 120, h // 2 - 30, 240, 52), mouse)
            _button(screen, font, "Tutorial", (w // 2 - 120, h // 2 + 38, 240, 52), mouse)
            _button(screen, font, "Settings", (w // 2 - 120, h // 2 + 106, 240, 52), mouse)
            _button(screen, font, "Quit", (w // 2 - 120, h // 2 + 174, 240, 52), mouse)
        elif page == "tutorial":
            _text(screen, title_font, "How to Play", (w // 2, h // 2 - 175))
            tutorial_lines = (
                "Goal: stand upright on the green goal tile.",
                "Move: arrow keys or W, A, S, D.",
                "Rotate the camera: Q / E.",
                "Pan the board: hold the middle mouse button and drag.",
                "Zoom: use the mouse wheel.",
                "Restart: R. Select a level: L. Return to menu: Esc.",
                "Standing upright on a fragile tile causes Game Over.",
            )
            for index, line in enumerate(tutorial_lines):
                _text(screen, small_font, line,
                      (w // 2, h // 2 - 95 + index * 38))
            _button(screen, font, "Back", (w // 2 - 120, h - 75, 240, 48), mouse)
        elif page == "settings":
            _text(screen, title_font, "Settings", (w // 2, h // 2 - 150))
            _text(screen, font, f"Volume: {round(volume * 100)}%", (w // 2, h // 2 - 105))
            pygame.draw.rect(screen, (105, 120, 145), (w // 2 - 150, h // 2 - 80, 300, 8), border_radius=4)
            pygame.draw.circle(screen, (245, 195, 75), (w // 2 - 150 + round(volume * 300), h // 2 - 76), 10)
            _text(screen, font, f"Brightness: {brightness:+d}%", (w // 2, h // 2 - 42))
            pygame.draw.rect(screen, (105, 120, 145), (w // 2 - 150, h // 2 - 20, 300, 8), border_radius=4)
            pygame.draw.circle(screen, (245, 195, 75), (w // 2 + round(brightness * 1.5), h // 2 - 16), 10)
            _button(screen, font, "Windowed / Fullscreen", (w // 2 - 150, h // 2 + 40, 300, 46), mouse)
            _text(screen, small_font, "Current mode: " + ("Fullscreen" if fullscreen else "Windowed"), (w // 2, h // 2 + 99))
            _button(screen, font, "Back", (w // 2 - 120, h // 2 + 125, 240, 48), mouse)
        elif page == "levels":
            _text(screen, title_font, "Select a level", (w // 2, 75))
            page_start = (selected_map // 7) * 7 if maps else 0
            visible_count = min(max(0, len(maps) - page_start), 7)
            list_top = h // 2 - visible_count * 24
            for index in range(page_start, page_start + visible_count):
                _, game_map = maps[index]
                label = f"{game_map.name}  ·  {game_map.difficulty}"
                rect = pygame.Rect(w // 2 - 250, list_top + (index - page_start) * 48, 500, 42)
                pygame.draw.rect(screen, (75, 102, 145) if index == selected_map else (48, 61, 83), rect, border_radius=7)
                _text(screen, font, label, rect.center)
            if not maps:
                _text(screen, font, "No JSON maps found in data/maps", (w // 2, h // 2))
            _button(screen, font, "Back", (w // 2 - 120, h - 75, 240, 48), mouse)
        elif page == "game" and maps and state and camera:
            game_map = maps[selected_map][1]
            broken_cells = {falling["cell"]} if falling else set()
            draw_map(screen, game_map.grid, camera, hidden_cells=broken_cells)
            if motion:
                draw_animated_block(
                    screen, _state_as_dict(motion["start"]),
                    _state_as_dict(motion["end"]),
                    motion["action"], min(1.0, motion["elapsed"] / 0.24), camera
                )
            elif falling:
                fall_progress = min(1.0, falling["elapsed"] / 0.55)
                fall_distance = 2.4 * fall_progress * fall_progress
                draw_block(screen, _state_as_dict(falling["state"]), camera,
                           height_offset=-fall_distance)
                # Vẽ lại nền phía trước khối để khối rơi bị che bởi các ô lân cận.
                depth_y = camera.project(*falling["cell"])[1]
                draw_front_tiles(screen, game_map.grid, camera, depth_y,
                                 hidden_cells=broken_cells)
            else:
                draw_block(screen, _state_as_dict(fallen_preview or state), camera)
            _button(screen, small_font, "Levels", (12, 12, 150, 42), mouse)
            _button(screen, small_font, "Restart", (172, 12, 120, 42), mouse)
            solver.draw(screen, small_font)
            _text(screen, small_font, game_map.name, (w // 2, h - 48))
            hint = "Move: UP, DOWN, LEFT, RIGHT | W, A, S, D | Q/E rotate"
            _text(screen, small_font, hint, (w // 2, h - 20))
            if message:
                banner = pygame.Surface((w, 66), pygame.SRCALPHA)
                banner.fill((12, 17, 26, 220))
                screen.blit(banner, (0, h // 2 - 33))
                _text(screen, font, message, (w // 2, h // 2))

        if brightness:
            shade = pygame.Surface((w, h), pygame.SRCALPHA)
            if brightness > 0:
                shade.fill((255, 255, 255, round(brightness * 1.5)))
            else:
                shade.fill((0, 0, 0, round(-brightness * 1.5)))
            screen.blit(shade, (0, 0))
        pygame.display.flip()

    solver.reset()
    pygame.quit()


if __name__ == "__main__":
    main()
