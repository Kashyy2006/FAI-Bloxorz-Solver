"""Controller regressions and an end-to-end solve/replay using real GUI moves."""

import os
import time
import unittest
from unittest.mock import patch
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from src.gui.manual.game import _move
from src.gui.solver.controller import SolverController
from src.gui.solver.replay import Replay, SPEEDS
from src.gui.solver.result import make_result
from .test_solver_gui_backend import load, start_of
from .test_solver_result import solved_result


class StubWorker:
    """Deliver a controlled response at the next controller update."""

    def __init__(self):
        self.result = None

    def start(self, *args):
        pass

    def discard(self):
        self.result = None

    def cancel(self):
        pass  # Intentionally leaves queued success to exercise controller defense.

    def poll(self):
        result, self.result = self.result, None
        return result


class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.game_map = load("basic_01.json")
        self.state = start_of(self.game_map)
        self.controller = SolverController(_move)
        self.controller.worker = StubWorker()

    def run_command(self, command, ready=True):
        self.controller.run(command, self.game_map, self.state, ready=ready)

    def loaded(self):
        self.run_command("BFS")
        self.controller.take_restore_state()
        self.controller.worker.result = solved_result(self.game_map, self.state)
        self.assertIsNone(self.controller.update(0, ready=False))
        self.run_command("PLAY")  # pause the automatically started replay

    def test_repeated_step_does_not_skip_and_waits_for_ready(self):
        self.loaded()
        self.run_command("STEP")
        self.run_command("STEP")
        self.assertEqual(self.controller.replay.index, 0)
        self.assertTrue(self.controller.busy)
        self.assertIsNone(self.controller.update(1, ready=False))
        self.assertEqual(self.controller.update(0, ready=True), "RIGHT")
        self.assertEqual(self.controller.replay.index, 1)
        self.assertIsNone(self.controller.update(1, ready=True))
        self.run_command("STEP")
        self.assertEqual(self.controller.update(0, ready=True), "RIGHT")
        self.assertTrue(self.controller.replay.done)

    def test_play_after_queued_step_does_not_emit_it_twice(self):
        self.loaded()
        self.run_command("STEP")
        self.run_command("PLAY")
        self.assertEqual(self.controller.update(0, ready=True), "RIGHT")
        self.assertIsNone(self.controller.update(0, ready=True))
        self.assertEqual(self.controller.update(1, ready=True), "RIGHT")
        self.assertEqual(self.controller.replay.index, 2)

    def test_stop_clears_pending_step_and_restores_owned_start_state(self):
        self.loaded()
        self.run_command("STEP")
        self.run_command("STOP")
        restored = self.controller.take_restore_state()
        self.assertEqual(restored, self.state)
        restored["cells"].clear()
        self.assertEqual(self.controller.start_state, self.state)
        self.assertEqual(self.controller.replay.index, 0)
        self.assertIsNone(self.controller.update(1, ready=True))

    def test_play_after_completion_restores_start_but_not_mid_animation(self):
        self.loaded()
        self.run_command("PLAY")
        self.controller.update(0, True)
        self.controller.update(1, True)
        self.run_command("PLAY", ready=False)
        self.assertIsNone(self.controller.take_restore_state())
        self.run_command("PLAY")
        self.assertEqual(self.controller.take_restore_state(), self.state)
        self.assertEqual(self.controller.update(0, True), "RIGHT")

    def test_reset_clears_restore_replay_and_queued_step(self):
        self.run_command("BFS")
        self.controller.reset()
        self.assertIsNone(self.controller.take_restore_state())
        self.assertIsNone(self.controller.start_state)
        self.assertIsNone(self.controller.result)
        self.assertFalse(self.controller.busy)
        self.assertIsNone(self.controller.update(1, True))
        self.loaded()
        self.run_command("STEP")
        self.controller.reset()
        self.assertIsNone(self.controller.update(1, True))

    def test_manual_move_invalidates_replay_and_restore(self):
        self.loaded()
        self.run_command("STEP")
        self.controller.on_manual_move()
        self.run_command("STOP")
        self.assertIsNone(self.controller.take_restore_state())
        self.assertIsNone(self.controller.update(1, True))
        self.assertFalse(self.controller.busy)

    def test_cancel_wins_over_success_already_waiting(self):
        self.run_command("BFS")
        self.controller.worker.result = solved_result(self.game_map, self.state)
        self.run_command("CANCEL")
        self.assertFalse(self.controller.can_run("CANCEL"))
        self.assertEqual(self.controller._stat_lines()[1][1], "CANCELLING")
        self.assertIsNone(self.controller.update(1, True))
        self.assertEqual(self.controller.result["status"], "CANCELLED")
        self.assertEqual(self.controller.replay.actions, [])
        self.assertFalse(self.controller.busy)

    def test_malformed_output_reports_error_instead_of_crashing_gui(self):
        for raw in ("bad JSON", [], 42, {"status": "SOLVED"},
                    {**solved_result(self.game_map, self.state), "metrics": []}):
            with self.subTest(raw=raw):
                self.run_command("BFS")
                self.controller.worker.result = raw
                self.assertIsNone(self.controller.update(1, True))
                self.assertEqual(self.controller.result["status"], "ERROR")
                self.assertTrue(self.controller.result["error"])
                self.controller._stat_lines()  # rendering data is still safe
                self.assertFalse(self.controller.busy)

    def test_unsupported_switch_is_an_error_not_a_replay_crash(self):
        self.controller.supported_actions = frozenset(("UP", "DOWN", "LEFT", "RIGHT"))
        self.run_command("BFS")
        self.controller.worker.result = solved_result(self.game_map, self.state,
                                                     actions=["SWITCH"])
        self.assertIsNone(self.controller.update(1, True))
        self.assertEqual(self.controller.result["status"], "ERROR")
        self.assertIn("SWITCH", self.controller.result["error"])

    def test_failed_search_does_not_start_replay(self):
        for status in ("UNSOLVABLE", "TIMEOUT", "ERROR"):
            with self.subTest(status=status):
                self.run_command("BFS")
                self.controller.worker.result = make_result(
                    self.game_map, self.state, "BFS", 60.0, status,
                    "failed" if status == "ERROR" else None)
                self.assertIsNone(self.controller.update(1, True))
                self.assertEqual(self.controller.result["status"], status)
                self.assertFalse(self.controller.replay.playing)

    def test_controls_during_animation_and_disabled_commands(self):
        self.loaded()
        self.run_command("PLAY")
        self.assertTrue(self.controller.handle_key(pygame.K_SPACE, self.game_map,
                                                  self.state, ready=False))
        self.assertFalse(self.controller.replay.playing)
        self.run_command("DFS", ready=False)
        self.assertFalse(self.controller.solving)
        self.assertEqual(self.controller.algorithm, "BFS")
        self.run_command("BFS")
        self.assertFalse(self.controller.can_run("PLAY"))
        self.assertFalse(self.controller.can_run("STOP"))
        self.run_command("STOP")
        self.assertTrue(self.controller.solving)

    def test_disabled_click_cannot_change_state(self):
        self.controller.panel_open = True
        self.controller.update(1, False)
        self.controller.replay.load([])
        for cmd, _, rect in self.controller._layout(900, 600):
            if cmd == "STEP":
                self.controller.handle_click(rect.center, (900, 600),
                                             self.game_map, self.state)
        self.assertFalse(self.controller.busy)

    def test_drawer_starts_closed_and_hidden_controls_ignore_clicks(self):
        self.assertFalse(self.controller.panel_open)
        _, _, button = self.controller._layout(900, 600)[0]
        self.assertFalse(self.controller.handle_click(
            button.center, (900, 600), self.game_map, self.state))
        self.assertFalse(self.controller.solving)
        for size in ((900, 600), (1200, 800)):
            toggle = self.controller._toggle_rect(*size)
            self.assertEqual(toggle.right, size[0])
            self.assertEqual(toggle.centery, size[1] // 4)
            self.assertTrue(self.controller.handle_click(
                toggle.center, size, self.game_map, self.state))
            self.assertTrue(self.controller.panel_open)
            toggle = self.controller._toggle_rect(*size)
            self.assertEqual(toggle.right, self.controller._panel_rect(*size).left)
            self.controller.handle_click(toggle.center, size, self.game_map, self.state)
            self.assertFalse(self.controller.panel_open)

    def test_drawer_slides_reverses_and_tracks_resize(self):
        controller = self.controller
        controller.handle_click(controller._toggle_rect(900, 600).center,
                                (900, 600), self.game_map, self.state)
        self.assertEqual(controller._panel_rect(900, 600).left, 900)
        controller.update(0.13, False)
        halfway = controller._panel_rect(900, 600).left
        self.assertGreater(halfway, 650)
        self.assertLess(halfway, 900)
        self.assertEqual(controller._panel_rect(1200, 800).left, halfway + 300)
        velocity = controller._panel_velocity
        controller.handle_click(controller._toggle_rect(900, 600).center,
                                (900, 600), self.game_map, self.state)
        self.assertEqual(controller._panel_rect(900, 600).left, halfway)
        self.assertEqual(controller._panel_velocity, velocity)
        controller.update(0.001, False)
        self.assertGreater(controller._panel_velocity, 0)
        controller.update(0.13, False)
        self.assertGreater(controller._panel_rect(900, 600).left, halfway)
        controller.update(1, False)
        self.assertEqual(controller._panel_rect(900, 600).left, 900)
        controller.panel_open = True
        controller.update(1, False)
        self.assertEqual(controller._panel_rect(900, 600).left, 650)

    def test_drawer_motion_is_consistent_across_frame_rates(self):
        positions = []
        for fps in (30, 60, 120):
            controller = SolverController(_move)
            controller.worker = StubWorker()
            controller.panel_open = True
            for _ in range(fps // 2):
                controller.update(1 / fps, False)
                self.assertGreaterEqual(controller._panel_progress, 0)
                self.assertLessEqual(controller._panel_progress, 1)
            positions.append(controller._panel_progress)
            controller.update(1, False)
            self.assertEqual(controller._panel_progress, 1)
            controller.panel_open = False
            controller.update(1, False)
            self.assertEqual(controller._panel_progress, 0)
        self.assertAlmostEqual(positions[0], positions[1])
        self.assertAlmostEqual(positions[1], positions[2])

    def test_moving_drawer_consumes_clicks_without_starting_solver(self):
        self.controller.panel_open = True
        self.controller.update(0.195, False)
        _, _, button = self.controller._layout(900, 600)[0]
        self.assertTrue(self.controller.handle_click(
            button.center, (900, 600), self.game_map, self.state))
        self.assertFalse(self.controller.solving)

    def test_closing_drawer_keeps_solution_and_replay_running(self):
        self.loaded()
        self.controller.panel_open = True
        self.run_command("PLAY")
        result = self.controller.result
        self.controller.handle_click(self.controller._toggle_rect(900, 600).center,
                                     (900, 600), self.game_map, self.state)
        self.assertFalse(self.controller.panel_open)
        self.assertIs(self.controller.result, result)
        self.assertTrue(self.controller.replay.playing)
        self.assertEqual(self.controller.update(0, True), "RIGHT")

    def test_first_action_is_immediate_at_every_speed_and_pause_is_stable(self):
        for index, speed in enumerate(SPEEDS):
            with self.subTest(speed=speed):
                replay = Replay()
                replay.speed_index = index
                replay.load(["UP", "DOWN"])
                replay.play()
                self.assertIsNone(replay.update(10, False))
                self.assertEqual(replay.update(0, True), "UP")
                replay.pause()
                self.assertIsNone(replay.update(10, True))
                replay.play()
                self.assertEqual(replay.update(0, True), "DOWN")
                self.assertTrue(replay.done)


class RealSolverReplayTest(unittest.TestCase):
    def test_game_loop_solves_and_accepts_pause_during_animation(self):
        from src.gui.manual import game

        for pause in (False, True):
            with self.subTest(pause_during_animation=pause):
                game_map = load("basic_01.json")
                controllers, drawn = [], []
                frame = 0

                def make_controller(**kwargs):
                    controller = SolverController(**kwargs)
                    controllers.append(controller)
                    return controller

                def events():
                    nonlocal frame
                    frame += 1
                    if frame == 1:
                        return [pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                                   button=1, pos=(450, 290))]
                    if frame == 2:
                        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
                    if frame == 3:
                        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)]
                    # Solve finishes very quickly on this map. Pause on the
                    # first frame after an action has been issued, before its
                    # 0.24-second animation can finish (each tick is 0.1 sec).
                    if (pause and controllers and controllers[0].replay.index == 1
                            and controllers[0].replay.playing):
                        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)]
                    if frame >= 40:
                        return [pygame.event.Event(pygame.QUIT)]
                    return []

                def tick(_fps):
                    time.sleep(0.001)  # allow the actual background thread to run
                    return 100

                with patch.object(game, "SolverController", side_effect=make_controller), \
                     patch.object(game, "_load_maps", return_value=[(None, game_map)]), \
                     patch.object(game, "BGM_DIR", Path(__file__).parent), \
                     patch.object(game, "draw_block", side_effect=lambda screen, state, camera:
                                  drawn.append(state)), \
                     patch.object(pygame.event, "get", side_effect=events), \
                     patch.object(pygame.time, "Clock") as clock:
                    clock.return_value.tick.side_effect = tick
                    try:
                        game.main()
                    finally:
                        for controller in controllers:
                            controller.reset()
                            if controller.worker._thread:
                                controller.worker._thread.join(3)
                        pygame.quit()
                self.assertTrue(drawn)
                if pause:
                    self.assertEqual(drawn[-1]["mode"], "HORIZONTAL")
                    self.assertEqual(drawn[-1]["cells"], [(1, 2), (1, 3)])
                else:
                    self.assertEqual(drawn[-1]["mode"], "UPRIGHT")
                    self.assertEqual(drawn[-1]["cells"], [(1, 4)])

    def test_all_algorithms_replay_from_current_state_to_goal(self):
        game_map = load("basic_01.json")
        # Start after a manual move, so solving from the level start would fail
        # the expected length and final-state checks.
        current = _move(start_of(game_map), "RIGHT", game_map)
        for algorithm in ("BFS", "DFS", "UCS", "ASTAR"):
            with self.subTest(algorithm=algorithm):
                controller = SolverController(_move)
                try:
                    controller.run(algorithm, game_map, current)
                    state = controller.take_restore_state()
                    deadline = time.monotonic() + 3
                    emitted = []
                    while time.monotonic() < deadline:
                        action = controller.update(1, ready=True)
                        if action:
                            emitted.append(action)
                            state = _move(state, action, game_map)
                            self.assertIsNotNone(state)
                        if not controller.busy:
                            break
                        time.sleep(0.001)
                    self.assertFalse(controller.busy)
                    self.assertEqual(controller.result["status"], "SOLVED")
                    self.assertEqual(emitted, ["RIGHT"])
                    self.assertEqual(controller.result["metrics"]["solution_length"], 1)
                    self.assertEqual(state["mode"], "UPRIGHT")
                    row, col = state["cells"][0]
                    self.assertEqual(game_map["grid"][row][col], "goal")
                finally:
                    controller.reset()
                    controller.worker._thread.join(3)

    def test_all_algorithms_solve_and_replay_advanced_bridge_and_split_from_mid_game(self):
        from src.gui.manual.game import _initial_state
        for filename, manual_moves in (
            ("advanced_bridge_01.json", ("RIGHT", "RIGHT")),
            ("advanced_split_01.json", ("RIGHT", "RIGHT", "SWITCH")),
        ):
            game_map = load(filename)
            current = _initial_state(game_map)
            for move in manual_moves:
                current = _move(current, move, game_map)
                self.assertIsNotNone(current)
            for algorithm in ("BFS", "DFS", "UCS", "ASTAR"):
                with self.subTest(map=filename, algorithm=algorithm):
                    controller = SolverController(_move)
                    try:
                        controller.run(algorithm, game_map, current)
                        state = controller.take_restore_state()
                        self.assertEqual(state, current)
                        deadline = time.monotonic() + 3
                        emitted = []
                        while time.monotonic() < deadline:
                            action = controller.update(1, ready=True)
                            if action:
                                emitted.append(action)
                                state = _move(state, action, game_map)
                                self.assertIsNotNone(state)
                            if not controller.busy:
                                break
                            time.sleep(0.001)
                        self.assertFalse(controller.busy)
                        self.assertEqual(controller.result["status"], "SOLVED")
                        self.assertEqual(emitted, controller.result["actions"])
                        self.assertEqual(state["mode"], "UPRIGHT")
                        row, col = state["cells"][0]
                        self.assertEqual(game_map["grid"][row][col], "goal")
                    finally:
                        controller.reset()
                        if controller.worker._thread:
                            controller.worker._thread.join(3)

    def test_error_panel_renders_with_headless_pygame(self):
        pygame.init()
        try:
            screen = pygame.display.set_mode((900, 600))
            game_map = load("basic_01.json")
            controller = SolverController(_move)
            controller.worker = StubWorker()
            controller.run("BFS", game_map, start_of(game_map))
            controller.worker.result = "invalid JSON"
            controller.update(0, False)
            controller.panel_open = True
            controller.update(1, False)
            controller.draw(screen, pygame.font.Font(None, 25))
            self.assertEqual(controller.result["status"], "ERROR")
        finally:
            pygame.quit()

