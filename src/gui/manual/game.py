"""Manual Pygame interface: menu, settings, level selection and basic play."""

import json
from pathlib import Path

import pygame

from .camera import Camera
from .renderer import draw_animated_block, draw_block, draw_map
from .settings import BACKGROUND_COLOR, FPS, HEIGHT, WIDTH

ROOT = Path(__file__).resolve().parents[3]
MAPS_DIR = ROOT / "data" / "maps"
BGM_DIR = ROOT / "data" / "bgm"


def _load_maps():
    maps = []
    for path in sorted(MAPS_DIR.glob("*.json")):
        try:
            with path.open(encoding="utf-8") as file:
                data = json.load(file)
            grid = data["grid"]
            if (grid and all(isinstance(row, list) for row in grid)
                    and all(len(row) == len(grid[0]) for row in grid)
                    and all(isinstance(cell, str) for row in grid for cell in row)):
                maps.append((path, data))
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            continue
    return maps


def _initial_state(game_map):
    row, col = game_map.get("start", (1, 1))
    return {"mode": "UPRIGHT", "cells": [(row, col)], "active": None}


def _move(state, action, grid):
    """Basic Bloxorz movement used until the shared engine is integrated."""
    mode = state["mode"]
    cells = state["cells"]
    dr, dc = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}[action]
    row, col = cells[0]

    if mode == "UPRIGHT":
        if action == "UP":
            result = ("VERTICAL", [(row - 2, col), (row - 1, col)])
        elif action == "DOWN":
            result = ("VERTICAL", [(row + 1, col), (row + 2, col)])
        elif action == "LEFT":
            result = ("HORIZONTAL", [(row, col - 2), (row, col - 1)])
        else:
            result = ("HORIZONTAL", [(row, col + 1), (row, col + 2)])
    elif mode == "HORIZONTAL":
        if action == "LEFT":
            result = ("UPRIGHT", [(row, col - 1)])
        elif action == "RIGHT":
            result = ("UPRIGHT", [(row, col + 2)])
        else:
            result = (mode, [(r + dr, c + dc) for r, c in cells])
    else:  # VERTICAL
        if action == "UP":
            result = ("UPRIGHT", [(row - 1, col)])
        elif action == "DOWN":
            result = ("UPRIGHT", [(row + 2, col)])
        else:
            result = (mode, [(r + dr, c + dc) for r, c in cells])

    next_mode, next_cells = result
    rows, cols = len(grid), len(grid[0])
    if any(r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] == "void"
           for r, c in next_cells):
        return None
    return {"mode": next_mode, "cells": next_cells, "active": None}


def _text(screen, font, value, center, color=(240, 243, 250)):
    surface = font.render(str(value), True, color)
    screen.blit(surface, surface.get_rect(center=center))


def _button(screen, font, label, rect, mouse_pos, color=(63, 83, 115)):
    box = pygame.Rect(rect)
    hovered = box.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (91, 123, 168) if hovered else color, box, border_radius=9)
    _text(screen, font, label, box.center)
    return box


def main():
    pygame.init()
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        tracks = sorted(path for path in BGM_DIR.iterdir()
                        if path.is_file() and path.suffix.lower() in {".mp3", ".ogg", ".wav"})
        if tracks:
            pygame.mixer.music.load(str(tracks[0]))
            pygame.mixer.music.set_volume(0.7)
            pygame.mixer.music.play(-1)
            print(f"Playing background music: {tracks[0].name}")
    except (pygame.error, OSError) as error:
        print(f"Could not start background music from {BGM_DIR}: {error}")

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Bloxorz")
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 58)
    font = pygame.font.Font(None, 34)
    small_font = pygame.font.Font(None, 25)

    maps = _load_maps()
    if not maps:
        print(f"No playable map JSON files found in {MAPS_DIR}")

    page = "menu"
    selected_map = 0
    state = None
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
                        page = "menu"
                    elif page != "menu":
                        page = "menu"
                    else:
                        running = False
                elif page == "game" and event.key == pygame.K_r and maps:
                    state = _initial_state(maps[selected_map][1])
                    motion = None
                    message = ""
                elif page == "game" and event.key == pygame.K_l:
                    page = "levels"
                elif page == "game" and event.key == pygame.K_q and camera:
                    camera.rotate(-1)
                elif page == "game" and event.key == pygame.K_e and camera:
                    camera.rotate(1)
                elif page == "game" and state and not message:
                    action = {
                        pygame.K_UP: "UP", pygame.K_w: "UP",
                        pygame.K_DOWN: "DOWN", pygame.K_s: "DOWN",
                        pygame.K_LEFT: "LEFT", pygame.K_a: "LEFT",
                        pygame.K_RIGHT: "RIGHT", pygame.K_d: "RIGHT",
                    }.get(event.key)
                    if action and motion is None and camera and not camera.rotating:
                        game_map = maps[selected_map][1]
                        moved = _move(state, action, game_map["grid"])
                        if moved is None:
                            message = "You fell! Press R to restart, L for levels."
                        else:
                            motion = {"start": state, "end": moved,
                                      "action": action, "elapsed": 0.0}
                elif page == "levels" and maps:
                    if event.key in (pygame.K_UP, pygame.K_LEFT):
                        selected_map = (selected_map - 1) % len(maps)
                    elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                        selected_map = (selected_map + 1) % len(maps)
                    elif event.key == pygame.K_RETURN:
                        game_map = maps[selected_map][1]
                        state = _initial_state(game_map)
                        camera = Camera(len(game_map["grid"][0]), len(game_map["grid"]), *screen.get_size())
                        motion = None
                        message = ""
                        page = "game"

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                w, h = screen.get_size()
                if page == "menu":
                    if pygame.Rect(w // 2 - 120, h // 2 - 30, 240, 52).collidepoint(event.pos):
                        page = "levels"
                    elif pygame.Rect(w // 2 - 120, h // 2 + 38, 240, 52).collidepoint(event.pos):
                        page = "settings"
                    elif pygame.Rect(w // 2 - 120, h // 2 + 106, 240, 52).collidepoint(event.pos):
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
                    elif pygame.Rect(w // 2 - 120, h // 2 + 112, 240, 48).collidepoint(event.pos):
                        page = "menu"
                elif page == "levels" and maps:
                    page_start = (selected_map // 7) * 7
                    page_count = min(7, len(maps) - page_start)
                    list_top = h // 2 - page_count * 42 // 2
                    for index in range(page_start, page_start + page_count):
                        rect = pygame.Rect(w // 2 - 250, list_top + (index - page_start) * 48, 500, 42)
                        if rect.collidepoint(event.pos):
                            selected_map = index
                            game_map = maps[selected_map][1]
                            state = _initial_state(game_map)
                            camera = Camera(len(game_map["grid"][0]), len(game_map["grid"]), *screen.get_size())
                            motion = None
                            message = ""
                            page = "game"
                            break
                    if pygame.Rect(w // 2 - 120, h - 75, 240, 48).collidepoint(event.pos):
                        page = "menu"
                elif page == "game":
                    if pygame.Rect(12, 12, 150, 42).collidepoint(event.pos):
                        page = "levels"
                    elif pygame.Rect(172, 12, 120, 42).collidepoint(event.pos):
                        state = _initial_state(maps[selected_map][1])
                        motion = None
                        message = ""

        if camera:
            camera.update(dt)
        if motion:
            motion["elapsed"] += dt
            if motion["elapsed"] >= 0.24:
                state = motion["end"]
                motion = None
                game_map = maps[selected_map][1]
                row, col = state["cells"][0]
                if state["mode"] == "UPRIGHT" and game_map["grid"][row][col] == "goal":
                    message = "Level complete! Press L for levels."

        screen.fill(BACKGROUND_COLOR)
        w, h = screen.get_size()
        mouse = pygame.mouse.get_pos()
        if page == "menu":
            _text(screen, title_font, "BLOXORZ", (w // 2, h // 2 - 130))
            _button(screen, font, "Play", (w // 2 - 120, h // 2 - 30, 240, 52), mouse)
            _button(screen, font, "Settings", (w // 2 - 120, h // 2 + 38, 240, 52), mouse)
            _button(screen, font, "Quit", (w // 2 - 120, h // 2 + 106, 240, 52), mouse)
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
                _, data = maps[index]
                label = f"{data.get('name', data.get('id', 'Unnamed'))}  ·  {data.get('difficulty', 'unknown')}"
                rect = pygame.Rect(w // 2 - 250, list_top + (index - page_start) * 48, 500, 42)
                pygame.draw.rect(screen, (75, 102, 145) if index == selected_map else (48, 61, 83), rect, border_radius=7)
                _text(screen, font, label, rect.center)
            if not maps:
                _text(screen, font, "No JSON maps found in data/maps", (w // 2, h // 2))
            _button(screen, font, "Back", (w // 2 - 120, h - 75, 240, 48), mouse)
        elif page == "game" and maps and state and camera:
            game_map = maps[selected_map][1]
            draw_map(screen, game_map["grid"], camera)
            if motion:
                draw_animated_block(
                    screen, motion["start"], motion["end"],
                    motion["action"], min(1.0, motion["elapsed"] / 0.24), camera
                )
            else:
                draw_block(screen, state, camera)
            _button(screen, small_font, "Levels", (12, 12, 150, 42), mouse)
            _button(screen, small_font, "Restart", (172, 12, 120, 42), mouse)
            _text(screen, small_font, f"{game_map.get('name', game_map.get('id', 'Level'))}  |  Arrows/WASD move  |  Q/E rotate  |  R restart  |  Esc menu", (w // 2, h - 24))
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

    pygame.quit()


if __name__ == "__main__":
    main()
