# Giao diện Pygame để chơi thủ công, chọn màn và chỉnh cài đặt.

import sys
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    __package__ = "src.gui.manual"

import pygame
from src.engine import (parse_map, load_map, initial_state, state_from_dict, state_to_dict,
                        transition, Mode, State, Status)
from src.solvers.solve import solve
from src.engine.serialization import normalize_snapshot
from src.engine.geometry import movement_pose
from src.engine.models import Action

from .camera import Camera
from .tile_info import draw_tile_labels, draw_tile_tooltip
from .text_panel import draw_text_panel
from .renderer import draw_animated_block, draw_block, draw_front_tiles, draw_map, draw_falling_block
from .animations import BridgeAnimator, BlockPose, FALL_DURATION, motion_duration
from .settings import BACKGROUND_COLOR, FPS, HEIGHT, WIDTH
from ..solver.controller import SolverController

ROOT = Path(__file__).resolve().parents[3]
MAPS_DIR = ROOT / "data" / "maps"
BGM_DIR = ROOT / "data" / "bgm"


class MapCatalog(list):
    """Playable maps plus diagnostics; remains list-compatible for GUI callers."""
    def __init__(self):
        super().__init__()
        self.errors = []


# Nạp các bản đồ hợp lệ bằng validator dùng chung của engine.
def _load_maps():
    maps = MapCatalog()
    for path in sorted(MAPS_DIR.glob("*.json")):
        try:
            maps.append((path, load_map(path)))
        except (OSError, ValueError) as error:
            maps.errors.append(f"{path.name}: {type(error).__name__}: {error}")
            print(f"Could not load map {path.name}: {error}")
    return maps



# Adapter chung: giữ nguyên cờ cầu khi chuyển giữa engine, renderer và solver.
def _state_as_dict(state, game_map=None):
    if game_map is not None:
        data = state_to_dict(game_map, state)
        return data
    return {"mode": state.mode.value, "cells": list(state.cells),
            "active": state.active, "bridges": state.bridges}


def _map_as_dict(game_map):
    switches = []
    for switch in game_map.switches:
        item = {"id": switch.id, "cell": list(switch.cell), "type": switch.type}
        if switch.type == "split":
            item.update(destinations=[list(c) for c in switch.destinations],
                        active_destination=switch.active_destination)
        else:
            effect = {"mode": switch.effect_mode, "targets": list(switch.targets)}
            if switch.effect_mode == "permanent":
                effect["open"] = switch.open
            item["effect"] = effect
        switches.append(item)
    return {"schema_version": 1, "id": game_map.id, "name": game_map.name,
            "difficulty": game_map.difficulty, "rows": game_map.rows, "cols": game_map.cols,
            "grid": [list(row) for row in game_map.grid], "start": list(game_map.start),
            "bridges": [{"id": b.id, "cells": [list(c) for c in b.cells],
                         "initial_open": b.initial_open} for b in game_map.bridges],
            "switches": switches,
            "source": {"kind": "original", "reference": "Runtime engine snapshot"}}


def _state_from_dict(state_data, game_map):
    return state_from_dict(game_map, normalize_snapshot(state_data, game_map.bridge_ids))


def _initial_state(game_map):
    model = parse_map(game_map) if isinstance(game_map, dict) else game_map
    return _state_as_dict(initial_state(model), model)


def _move(state_data, action, game_map):
    model = parse_map(game_map) if isinstance(game_map, dict) else game_map
    state = _state_from_dict(state_data, model)
    result = transition(model, state, action)
    if result.status is Status.LOST:
        return None
    if result.status is Status.INVALID:
        return dict(state_data)
    return _state_as_dict(result.next_state, model)


def _visible_grid(game_map, state_data):
    model = parse_map(game_map) if isinstance(game_map, dict) else game_map
    state = _state_from_dict(state_data, model)
    grid = [list(row) for row in model.grid]
    for group, opened in zip(model.bridges, state.bridges):
        if not opened:
            for row, col in group.cells:
                grid[row][col] = "void"
    return grid


# Tạo tư thế đích chỉ để diễn hoạt ảnh của nước đi engine báo thua.
def _failed_move_preview(state, action):
    mode, cells, active = movement_pose(state, Action(action))
    return BlockPose(mode, cells, active, state.bridges)


def _fall_support(game_map, state, reason, events):
    flags = dict(zip(game_map.bridge_ids, state.bridges))
    for event in events:
        if event["type"] == "BRIDGE_CHANGED":
            flags[event["bridge_id"]] = event["after"]
    groups = {cell: b.id for b in game_map.bridges for cell in b.cells}
    supported = set()
    for cell in state.cells:
        tile = game_map.tile_at(cell)
        if tile == "void":
            continue
        if tile == "bridge" and not flags[groups[cell]]:
            continue
        if tile == "fragile" and reason == "FRAGILE_UPRIGHT":
            continue
        supported.add(cell)
    return supported


# Đổi hướng phím theo góc camera để phím luôn đi theo góc nhìn.
def _action_from_view(action, camera_angle):
    if action == "SWITCH":
        return action
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




def _level_layout(width, height, count, selected):
    """Shared drawing/click geometry; fit rows above pagination and Back."""
    page_size = max(1, min(7, (height - 300) // 48))
    page_count = max(1, (count + page_size - 1) // page_size)
    page = min(selected // page_size, page_count - 1) if count else 0
    start = page * page_size
    visible = min(page_size, max(0, count - start))
    row_width = min(620, max(160, width - 40))
    top = 120
    return {"size": page_size, "page": page, "pages": page_count,
            "rows": [(i, pygame.Rect((width-row_width)//2, top+(i-start)*48, row_width, 42))
                     for i in range(start, start+visible)],
            "previous": pygame.Rect(width//2-210, height-136, 160, 42),
            "next": pygame.Rect(width//2+50, height-136, 160, 42),
            "back": pygame.Rect(width//2-120, height-75, 240, 48)}


def _change_level_page(selected, count, layout, delta):
    if not count:
        return selected
    page = max(0, min(layout["pages"]-1, layout["page"]+delta))
    return selected if page == layout["page"] else page * layout["size"]


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
    map_errors_open = False
    map_error_scroll = 0
    if not maps:
        print(f"No playable map JSON files found in {MAPS_DIR}")
    solver = SolverController(move_fn=_move, solve_fn=solve,
                              supported_actions=("UP", "DOWN", "LEFT", "RIGHT", "SWITCH"))
    bridge_visuals = BridgeAnimator()
    bridge_replay = False
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

    def reset_play(snapshot=None, *, recenter=False):
        nonlocal state, motion, falling, fallen_preview, game_over_pending, message, camera, bridge_replay
        game_map = maps[selected_map][1]
        if snapshot is None:
            solver.reset()
        state = initial_state(game_map) if snapshot is None else _state_from_dict(snapshot, game_map)
        bridge_visuals.reset(game_map, state)
        bridge_replay = False
        motion = falling = fallen_preview = None
        game_over_pending = False
        message = ""
        if recenter:
            camera = Camera(game_map.cols, game_map.rows, *screen.get_size())

    def leave_play(destination):
        nonlocal page, motion, falling, fallen_preview, game_over_pending, message
        solver.reset()
        motion = falling = fallen_preview = None
        game_over_pending = False
        message = ""
        page = destination

    def begin_move(action, *, manual=False):
        nonlocal motion, game_over_pending, message
        game_map = maps[selected_map][1]
        result = transition(game_map, state, action)
        if result.status is Status.INVALID:
            if not manual:
                message = f"Replay stopped: {result.reason or result.status.value}."
            return False
        if manual:
            solver.on_manual_move()
        game_over_pending = result.status is Status.LOST
        motion = {"start": state,
                  "end": _failed_move_preview(state, action) if game_over_pending else result.next_state,
                  "action": action, "elapsed": 0.0, "events": result.events,
                  "status": result.status, "reason": result.reason, "map": game_map,
                  "replay": not manual}
        return True

    while running:
        dt = clock.tick(FPS) / 1000.0
        bridge_visuals.update(dt * (solver.replay.speed if bridge_replay else 1.0))
        mouse = pygame.mouse.get_pos()
        # Nhận thao tác bàn phím/chuột và cập nhật trang hoặc trạng thái ván.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif map_errors_open and event.type != pygame.VIDEORESIZE:
                if event.type == pygame.MOUSEWHEEL:
                    map_error_scroll = max(0, map_error_scroll - event.y * 3)
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_F2):
                    map_errors_open = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    map_errors_open = False
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                screen = pygame.display.set_mode((max(WIDTH, event.w), max(HEIGHT, event.h)), pygame.RESIZABLE)
                if camera:
                    camera.resize(*screen.get_size())
            elif event.type == pygame.MOUSEWHEEL and page == "game" and camera:
                if not solver.scroll_error(event.y):
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
                if page == "levels" and event.key == pygame.K_F2:
                    map_errors_open = bool(getattr(maps, "errors", []))
                    map_error_scroll = 0
                elif page == "levels" and event.key == pygame.K_F5:
                    maps = _load_maps()
                    selected_map = min(selected_map, max(0, len(maps)-1))
                elif event.key == pygame.K_ESCAPE:
                    if page == "game":
                        leave_play("menu")
                    elif page != "menu":
                        page = "menu"
                    else:
                        running = False
                elif page == "game" and event.key == pygame.K_r and maps:
                    reset_play()
                elif page == "game" and event.key == pygame.K_l:
                    leave_play("levels")
                elif page == "game" and event.key == pygame.K_q and camera:
                    camera.rotate(-1)
                elif page == "game" and event.key == pygame.K_e and camera:
                    camera.rotate(1)
                elif (page == "game" and maps and state and not game_over_pending
                      and solver.handle_key(event.key,
                                            _map_as_dict(maps[selected_map][1]),
                                            _state_as_dict(state, maps[selected_map][1]),
                                            ready=motion is None and not bridge_visuals.busy)):
                    restore = solver.take_restore_state()
                    if restore is not None:
                        reset_play(restore)
                elif (page == "game" and state and not message
                      and not game_over_pending and not solver.busy):
                    view_action = {
                        pygame.K_UP: "UP", pygame.K_w: "UP",
                        pygame.K_DOWN: "DOWN", pygame.K_s: "DOWN",
                        pygame.K_LEFT: "LEFT", pygame.K_a: "LEFT",
                        pygame.K_RIGHT: "RIGHT", pygame.K_d: "RIGHT",
                        pygame.K_TAB: "SWITCH",
                    }.get(event.key)
                    if (view_action and motion is None and not bridge_visuals.busy
                            and camera and not camera.rotating):
                        action = _action_from_view(view_action, camera.angle)
                        begin_move(action, manual=True)
                elif page == "levels" and maps:
                    layout = _level_layout(*screen.get_size(), len(maps), selected_map)
                    if event.key == pygame.K_UP:
                        selected_map = (selected_map - 1) % len(maps)
                    elif event.key == pygame.K_DOWN:
                        selected_map = (selected_map + 1) % len(maps)
                    elif event.key in (pygame.K_LEFT, pygame.K_PAGEUP):
                        selected_map = _change_level_page(selected_map, len(maps), layout, -1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN):
                        selected_map = _change_level_page(selected_map, len(maps), layout, 1)
                    elif event.key == pygame.K_RETURN:
                        reset_play(recenter=True)
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
                elif page == "levels":
                    if (getattr(maps, "errors", [])
                            and pygame.Rect(w-310, 8, 298, 32).collidepoint(event.pos)):
                        map_errors_open = True
                        map_error_scroll = 0
                        continue
                    layout = _level_layout(w, h, len(maps), selected_map)
                    for direction, delta in (("previous", -1), ("next", 1)):
                        if layout[direction].collidepoint(event.pos):
                            selected_map = _change_level_page(selected_map, len(maps), layout, delta)
                    for index, rect in layout["rows"]:
                        if rect.collidepoint(event.pos):
                            selected_map = index
                            reset_play(recenter=True)
                            page = "game"
                            break
                    if layout["back"].collidepoint(event.pos):
                        page = "menu"
                elif page == "game":
                    if (maps and state and not game_over_pending
                            and solver.handle_click(event.pos, (w, h),
                                                    _map_as_dict(maps[selected_map][1]),
                                                    _state_as_dict(state, maps[selected_map][1]),
                                                    ready=motion is None and not bridge_visuals.busy)):
                        restore = solver.take_restore_state()
                        if restore is not None:
                            reset_play(restore)
                    elif pygame.Rect(12, 12, 150, 42).collidepoint(event.pos):
                        leave_play("levels")
                    elif pygame.Rect(172, 12, 120, 42).collidepoint(event.pos):
                        reset_play()

        # Cập nhật camera, phát lại lời giải và hoàn tất hoạt ảnh di chuyển.
        if camera:
            camera.update(dt)
        if page == "game" and maps and state and camera:
            ready = (motion is None and not message and not game_over_pending
                     and not camera.rotating and not bridge_visuals.busy)
            action = solver.update(dt, ready)
            if action:
                begin_move(action)
        if motion:
            motion["elapsed"] += dt * (solver.replay.speed if motion.get("replay") else 1.0)
            if motion["elapsed"] >= motion_duration(motion):
                status = motion["status"]
                bridge_replay = motion.get("replay", False)
                bridge_visuals.trigger(motion.get("events", ()))
                if status is Status.LOST:
                    falling = {"state": motion["end"], "cell": motion["end"].cells[0],
                               "broken": motion.get("reason") == "FRAGILE_UPRIGHT",
                               "supported": _fall_support(motion["map"], motion["end"],
                                                          motion.get("reason"), motion.get("events", ())),
                               "action": motion["action"], "elapsed": 0.0, "replay": motion.get("replay", False)}
                else:
                    state = motion["end"]
                motion = None
                if status is Status.WON:
                    message = "Level complete! Press L for levels."

        if falling:
            # Chờ hiệu ứng rơi kết thúc rồi mới thông báo game over.
            falling["elapsed"] += dt * (solver.replay.speed if falling.get("replay") else 1.0)
            if falling["elapsed"] >= FALL_DURATION:
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
            errors = getattr(maps, "errors", [])
            if errors:
                _button(screen, small_font, f"Invalid maps: {len(errors)} | F2 details",
                        (w-310, 8, 298, 32), mouse, color=(115, 55, 45))
            _text(screen, title_font, "Select a level", (w // 2, 55))
            _text(screen, small_font, "Up/Down select | Left/Right pages | Enter play | F5 reload",
                  (w // 2, 95))
            layout = _level_layout(w, h, len(maps), selected_map)
            for index, rect in layout["rows"]:
                _, game_map = maps[index]
                label = f"{index+1}. {game_map.name}  |  {game_map.difficulty}"
                while font.size(label)[0] > rect.width - 24 and len(label) > 4:
                    label = label[:-4] + "..."
                pygame.draw.rect(screen, (75, 102, 145) if index == selected_map else (48, 61, 83), rect, border_radius=7)
                _text(screen, font, label, rect.center)
            if not maps:
                _text(screen, font, "No valid maps in data/maps. F2 errors | F5 reload", (w // 2, h // 2))
            for key, label, enabled in (("previous", "< Previous", layout["page"] > 0),
                                        ("next", "Next >", layout["page"]+1 < layout["pages"])):
                if enabled:
                    _button(screen, small_font, label, layout[key], mouse)
                else:
                    pygame.draw.rect(screen, (38, 46, 60), layout[key], border_radius=9)
                    _text(screen, small_font, label, layout[key].center, (110, 120, 135))
            _text(screen, small_font, f'{layout["page"]+1} / {layout["pages"]}',
                  (w//2, h-115))
            _button(screen, font, "Back", layout["back"], mouse)
        elif page == "game" and maps and state and camera:
            game_map = maps[selected_map][1]
            broken_cells = {falling["cell"]} if falling and falling["broken"] else set()
            bridge_levels = bridge_visuals.tile_levels(game_map)
            draw_map(screen, game_map.grid, camera, hidden_cells=broken_cells,
                     bridge_levels=bridge_levels)
            draw_tile_labels(screen, game_map, camera, bridge_levels, broken_cells)
            if motion:
                draw_animated_block(
                    screen, _state_as_dict(motion["start"]),
                    _state_as_dict(motion["end"]),
                    motion["action"], min(1.0, motion["elapsed"] / motion_duration(motion)), camera
                )
            elif falling:
                fall_progress = min(1.0, falling["elapsed"] / FALL_DURATION)
                draw_falling_block(screen, _state_as_dict(falling["state"]), camera,
                                   fall_progress, falling["action"], falling["supported"])
                cells = falling["state"].cells
                depth_y = sum(camera.project(*cell)[1] for cell in cells) / len(cells)
                draw_front_tiles(screen, game_map.grid, camera, depth_y,
                                 hidden_cells=broken_cells, bridge_levels=bridge_levels)
            else:
                draw_block(screen, _state_as_dict(fallen_preview or state), camera)
            _button(screen, small_font, "Levels", (12, 12, 150, 42), mouse)
            _button(screen, small_font, "Restart", (172, 12, 120, 42), mouse)
            if (mouse[1] > 60 and mouse[1] < h-65 and not solver.error_details_open
                    and not solver._toggle_rect(w, h).collidepoint(mouse)
                    and not (solver._panel_progress > 0 and solver._panel_rect(w, h).collidepoint(mouse))):
                draw_tile_tooltip(screen, small_font, game_map, state, camera, mouse,
                                  bridge_levels, broken_cells)
            solver.draw(screen, small_font)
            _text(screen, small_font, game_map.name, (w // 2, h - 48))
            hint = "Move: UP, DOWN, LEFT, RIGHT | W, A, S, D | Q/E rotate"
            _text(screen, small_font, hint, (w // 2, h - 20))
            if message:
                banner = pygame.Surface((w, 66), pygame.SRCALPHA)
                banner.fill((12, 17, 26, 220))
                screen.blit(banner, (0, h // 2 - 33))
                _text(screen, font, message, (w // 2, h // 2))

        if map_errors_open:
            map_error_scroll = draw_text_panel(
                screen, small_font, "Invalid maps | F2/Esc/click close | Wheel scroll",
                "The following files were skipped. Fix the file, then press F5 to reload.\n\n"
                + "\n\n".join(getattr(maps, "errors", [])), map_error_scroll)

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
