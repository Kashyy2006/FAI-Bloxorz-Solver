"""Regressions for lifecycle, shared costs, snapshots and heuristic metadata."""
import copy
import json
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
from pathlib import Path
import unittest
from unittest.mock import patch

import pygame
from src.contracts import GOAL_INDICATOR, REVERSE_BFS, MANHATTAN
from src.engine import initial_state, load_map, parse_map, state_to_dict, step_cost, successors
from src.gui.manual import game
from src.gui.solver.controller import SolverController
from src.gui.solver.result import validate_result
from src.solvers.common.schema import validate_payload
from src.solvers.costs.calc import heuristic_name
from src.solvers.solve import solve
from benchmarks.run import _validate_result

ROOT = Path(__file__).resolve().parents[2]


class IntegrationRegressionTest(unittest.TestCase):
    def test_changing_levels_during_roll_or_fall_discards_old_animation(self):
        grid = [["void"] * 6 for _ in range(3)]
        grid[0][0] = "goal"
        grid[1][2] = grid[1][3] = "floor"
        first = parse_map({"schema_version": 1, "id": "fall", "name": "fall",
                           "difficulty": "easy", "rows": 3, "cols": 6,
                           "grid": grid, "start": [1, 2], "bridges": [], "switches": [],
                           "source": {"kind": "original", "reference": "regression"}})
        second = load_map(ROOT / "data/maps/advanced_bridge_01.json")
        # Old preview reaches (1,4), a bridge on the NEW map, without any old bridge flags.
        for delay in (0, 4):
            for leave in (pygame.K_l, pygame.K_ESCAPE, "click"):
                with self.subTest(delay=delay, leave=leave):
                    frame, falls, final_states = 0, [], []
                    leave_frame = 4 + delay

                    def events():
                        nonlocal frame
                        frame += 1
                        keys = {2: pygame.K_RETURN, 3: pygame.K_RIGHT,
                                leave_frame + 1: pygame.K_DOWN,
                                leave_frame + 2: pygame.K_RETURN}
                        if frame == 1 or (leave == pygame.K_ESCAPE and frame == leave_frame + 1):
                            return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(450, 290))]
                        if frame == leave_frame:
                            return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(50, 30))
                                    if leave == "click" else pygame.event.Event(pygame.KEYDOWN, key=leave)]
                        if leave == pygame.K_ESCAPE:
                            keys[leave_frame + 2] = pygame.K_DOWN
                            keys[leave_frame + 3] = pygame.K_RETURN
                        if frame in keys:
                            return [pygame.event.Event(pygame.KEYDOWN, key=keys[frame])]
                        return [pygame.event.Event(pygame.QUIT)] if frame >= 20 else []

                    with patch.object(game, "_load_maps", return_value=[(None, first), (None, second)]), \
                         patch.object(pygame.event, "get", side_effect=events), \
                         patch.object(pygame.time, "Clock") as clock, \
                         patch.object(game, "draw_falling_block", side_effect=lambda *a: falls.append(frame)), \
                         patch.object(game, "draw_block", side_effect=lambda screen, state, camera: final_states.append(state)):
                        clock.return_value.tick.return_value = 100
                        game.main()
                    self.assertTrue(final_states)
                    self.assertEqual(final_states[-1]["cells"], list(initial_state(second).cells))
                    self.assertTrue(all(f < leave_frame for f in falls))

    def test_invalid_tab_keeps_loaded_solution_and_resize_keeps_controls_visible(self):
        model = load_map(ROOT / "data/maps/basic_01.json")
        frame, controllers, sizes = 0, [], []

        def factory(**kwargs):
            controller = SolverController(**kwargs)
            controllers.append(controller)
            return controller

        def events():
            nonlocal frame
            frame += 1
            if frame == 1:
                return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(450, 290))]
            if frame == 2:
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
            if frame == 3:
                controllers[0].replay.load(["RIGHT", "RIGHT"])
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB),
                        pygame.event.Event(pygame.VIDEORESIZE, w=320, h=240)]
            self.assertEqual(controllers[0].replay.actions, ["RIGHT", "RIGHT"])
            sizes.append(pygame.display.get_surface().get_size())
            return [pygame.event.Event(pygame.QUIT)]

        with patch.object(game, "_load_maps", return_value=[(None, model)]), \
             patch.object(game, "SolverController", side_effect=factory), \
             patch.object(pygame.event, "get", side_effect=events), \
             patch.object(pygame.time, "Clock") as clock:
            clock.return_value.tick.return_value = 100
            game.main()
        self.assertEqual(sizes, [(900, 600)])

    def test_actual_heuristic_is_accepted_by_gui_and_benchmark(self):
        for filename, expected in (("basic_01.json", REVERSE_BFS),
                                   ("advanced_bridge_01.json", GOAL_INDICATOR)):
            raw = json.loads((ROOT / "data/maps" / filename).read_text(encoding="utf-8"))
            model = parse_map(raw)
            snapshot = state_to_dict(model, initial_state(model))
            result = solve(model, initial_state(model), "ASTAR", timeout_s=5)
            self.assertEqual(result["status"], "SOLVED")
            self.assertEqual(result["heuristic"], expected)
            validate_result(result, raw, snapshot, "ASTAR", 5)
            _validate_result(result, {"map_id": model.id, "start_state": snapshot}, "ASTAR", 5)
        large = copy.deepcopy(raw)
        large.update(id="large", rows=25, cols=25, grid=[["floor"] * 25 for _ in range(25)],
                     start=[0, 0], bridges=[], switches=[])
        large["grid"][0][3] = "goal"
        model = parse_map(large)
        result = solve(model, initial_state(model), "ASTAR", timeout_s=5)
        self.assertEqual(heuristic_name(model), MANHATTAN)
        self.assertEqual(result["heuristic"], MANHATTAN)
        self.assertEqual(result["status"], "SOLVED")

    def test_cost_api_delegates_and_all_result_layers_reject_negative_measurements(self):
        model = load_map(ROOT / "data/maps/basic_01.json")
        state = initial_state(model)
        successor = successors(model, state)[0]
        with patch("src.solvers.costs.calc.calculate_step_cost", return_value=17) as cost:
            self.assertEqual(step_cost(model, state, successor.action, successor.state), 17)
            cost.assert_called_once_with(model, state, successor.state, successor.action)
        result = solve(model, state, "BFS")
        result["metrics"]["expanded_nodes"] = -1
        with self.assertRaises(ValueError):
            validate_payload(result)

    def test_full_error_details_can_scroll_to_last_character(self):
        pygame.init()
        try:
            controller = SolverController(move_fn=None)
            controller.result = {"status": "ERROR", "error": "ASTAR: ValueError: " + "x" * 3000 + "END"}
            controller.run("ERROR_DETAILS", {}, {})
            self.assertTrue(controller.error_details_open)
            self.assertTrue(controller.scroll_error(-1000))
            rendered = []
            with patch.object(controller, "_text", side_effect=lambda screen, font, value, pos, *a: rendered.append(value)):
                controller.draw(pygame.Surface((900, 600)), pygame.font.Font(None, 25))
            self.assertTrue(rendered[-1].endswith("END"))
            controller.run("ERROR_DETAILS", {}, {})
            self.assertFalse(controller.error_details_open)
        finally:
            pygame.quit()
