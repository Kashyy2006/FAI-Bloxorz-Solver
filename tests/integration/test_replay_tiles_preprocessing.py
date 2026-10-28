"""Replay wall time, map diagnostics, tile picking and A* preprocessing."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import pygame
from src.engine import initial_state, load_map
from src.gui.manual import game, tile_info
from src.gui.manual.camera import Camera
from src.gui.solver.replay import Replay, SPEEDS
from src.solvers.costs import calc
from src.solvers.solve import solve

ROOT = Path(__file__).resolve().parents[2]


class ReplayTimingTest(unittest.TestCase):
    def test_busy_animation_counts_towards_start_to_start_delay(self):
        replay = Replay()
        replay.load(["RIGHT"] * 4)
        replay.play()
        self.assertEqual(replay.update(0, True), "RIGHT")
        self.assertIsNone(replay.update(.24, False))
        self.assertIsNone(replay.update(.20, True))
        self.assertEqual(replay.update(.011, True), "RIGHT")

    def test_four_times_speed_in_real_game_loop_including_bridge_and_split(self):
        for filename in ("basic_01.json", "advanced_bridge_01.json", "advanced_split_01.json"):
            durations = []
            for speed in (1.0, 4.0):
                with self.subTest(map=filename, speed=speed):
                    model = load_map(ROOT / "data/maps" / filename)
                    result = solve(model, initial_state(model), "BFS")
                    self.assertEqual(result["status"], "SOLVED")
                    frame, start_frame, finish_frame = 0, 0, 0
                    controllers = []

                    from src.gui.solver.controller import SolverController
                    def factory(**kwargs):
                        controller = SolverController(**kwargs)
                        controllers.append(controller)
                        return controller

                    def events():
                        nonlocal frame, start_frame
                        frame += 1
                        if frame == 1:
                            return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(450, 290))]
                        if frame == 2:
                            return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
                        if frame == 3:
                            controller = controllers[0]
                            controller.replay.speed_index = SPEEDS.index(speed)
                            controller.replay.load(result["actions"])
                            controller.replay.play()
                            start_frame = frame
                        return [pygame.event.Event(pygame.QUIT)] if finish_frame or frame > 3000 else []

                    original_text = game._text
                    def text(screen, font, value, *args, **kwargs):
                        nonlocal finish_frame
                        if str(value).startswith("Level complete!") and not finish_frame:
                            finish_frame = frame
                        return original_text(screen, font, value, *args, **kwargs)

                    with patch.object(game, "_load_maps", return_value=[(None, model)]), \
                         patch.object(game, "SolverController", side_effect=factory), \
                         patch.object(pygame.event, "get", side_effect=events), \
                         patch.object(pygame.time, "Clock") as clock, \
                         patch.object(game, "_text", side_effect=text):
                        clock.return_value.tick.return_value = 5
                        game.main()
                    self.assertGreater(finish_frame, start_frame)
                    durations.append((finish_frame-start_frame)*.005)
            self.assertAlmostEqual(durations[0] / durations[1], 4, delta=.25)


class TileAndMapDiagnosticsTest(unittest.TestCase):
    def test_picking_respects_rotation_zoom_and_pan(self):
        model = load_map(ROOT / "data/maps/advanced_bridge_01.json")
        camera = Camera(model.cols, model.rows, 900, 600)
        for angle in (0, 45, 90, 180, 270):
            for zoom in (.4, 1, 2.5):
                camera.angle, camera.zoom = angle, zoom
                camera.move(7, -3)
                for cell in ((1, 1), (1, 4)):
                    with self.subTest(angle=angle, zoom=zoom, cell=cell):
                        self.assertEqual(tile_info.hovered_tile(model, camera, camera.project(*cell)), cell)
        description = tile_info.tile_description(model, initial_state(model), (1, 4))
        self.assertEqual(description, "Bridge [1, 4]")

    def test_bad_map_is_reported_and_good_map_remains_playable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "broken.json").write_text('{"grid": ', encoding="utf-8")
            (path / "good.json").write_bytes((ROOT / "data/maps/basic_01.json").read_bytes())
            with patch.object(game, "MAPS_DIR", path):
                catalog = game._load_maps()
        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0][1].id, "basic_01")
        self.assertEqual(len(catalog.errors), 1)
        self.assertIn("broken.json: ValueError:", catalog.errors[0])
        self.assertIn("invalid JSON at line 1", catalog.errors[0])

    def test_diagnostics_visible_even_when_every_map_is_invalid(self):
        catalog = game.MapCatalog()
        catalog.errors.append("broken.json: ValueError: grid rows do not match")
        frame, messages = 0, []
        def events():
            nonlocal frame
            frame += 1
            if frame == 1:
                return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(450, 290))]
            if frame == 2:
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F2)]
            return [pygame.event.Event(pygame.QUIT)]
        def panel(screen, font, title, text, scroll):
            messages.append(text)
            return 0
        with patch.object(game, "_load_maps", return_value=catalog), \
             patch.object(pygame.event, "get", side_effect=events), \
             patch.object(game, "draw_text_panel", side_effect=panel):
            game.main()
        self.assertTrue(any(catalog.errors[0] in text for text in messages))


class PreprocessingTest(unittest.TestCase):
    def setUp(self):
        self.model = load_map(ROOT / "data/maps/basic_01.json")

    def test_each_timed_search_builds_its_own_graph_despite_standalone_cache(self):
        calc._reverse_bfs_distances(self.model)
        with patch.object(calc, "_build_reverse_bfs_distances", wraps=calc._build_reverse_bfs_distances) as build:
            for _ in range(2):
                result = solve(self.model, initial_state(self.model), "ASTAR")
                self.assertEqual(result["status"], "SOLVED")
            self.assertEqual(build.call_count, 2)

    def test_cancel_and_timeout_interrupt_graph_preprocessing_before_expansion(self):
        original = calc._build_reverse_bfs_distances
        for status in ("CANCELLED", "TIMEOUT"):
            with self.subTest(status=status):
                event, clock = threading.Event(), [0.0]
                def build(model, check_stop):
                    calls = 0
                    def guard():
                        nonlocal calls
                        calls += 1
                        if calls == 3:
                            if status == "CANCELLED":
                                event.set()
                            else:
                                clock[0] = 2.0
                        check_stop()
                    return original(model, guard)
                with patch.object(calc, "_build_reverse_bfs_distances", side_effect=build), \
                     patch("src.solvers.common.runtime.perf_counter", side_effect=lambda: clock[0]):
                    result = solve(self.model, initial_state(self.model), "ASTAR", timeout_s=1, cancel_event=event)
                self.assertEqual(result["status"], status)
                self.assertEqual(result["metrics"]["expanded_nodes"], 0)
                self.assertIsNone(result["actions"])
                if status == "TIMEOUT":
                    self.assertEqual(result["metrics"]["search_time_s"], 2.0)
