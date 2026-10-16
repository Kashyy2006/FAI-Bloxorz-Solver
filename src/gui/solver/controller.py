"""Pygame side of the solver GUI: panel, statistics, input and replay glue.

Usage from the game loop (see src/gui/manual/game.py):
    solver = SolverController(move_fn=_move)
    solver.handle_key(...) / solver.handle_click(...)   # input
    restore = solver.take_restore_state()               # apply to game state
    action = solver.update(dt, ready)                   # replay action or None
    solver.draw(screen, small_font)
"""

import copy
import functools
import math

import pygame

from . import placeholder_solver
from .replay import Replay
from .result import make_result, validate_result
from .worker import SolverWorker

PANEL_W = 250
TOGGLE_W = 36
TOGGLE_H = 48
PANEL_SPRING_RATE = 16.0
ALGORITHMS = ("BFS", "DFS", "UCS", "ASTAR")
ALGO_LABELS = {"BFS": "1  BFS", "DFS": "2  DFS", "UCS": "3  UCS", "ASTAR": "4  A*"}
KEYS = {
    pygame.K_1: "BFS", pygame.K_2: "DFS", pygame.K_3: "UCS", pygame.K_4: "ASTAR",
    pygame.K_c: "CANCEL", pygame.K_SPACE: "PLAY", pygame.K_n: "STEP",
    pygame.K_x: "STOP", pygame.K_f: "SPEED",
}
STATUS_COLORS = {
    "SOLVED": (110, 220, 130), "UNSOLVABLE": (240, 170, 90),
    "TIMEOUT": (240, 200, 90), "CANCELLED": (180, 180, 190),
    "ERROR": (240, 100, 100), "SOLVING": (120, 190, 255),
    "CANCELLING": (180, 180, 190),
}


def _format_bytes(value):
    if value is None:
        return "-"
    for unit in ("B", "KB", "MB"):
        if value < 1024 or unit == "MB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024


def _fmt(value, pattern="{}"):
    return "-" if value is None else pattern.format(value)


class SolverController:
    def __init__(self, move_fn, solve_fn=None, timeout_s=60.0,
                 supported_actions=("UP", "DOWN", "LEFT", "RIGHT")):
        if solve_fn is None:
            solve_fn = functools.partial(placeholder_solver.solve, move_fn=move_fn)
        self.worker = SolverWorker(solve_fn)
        self.replay = Replay()
        self.timeout_s = timeout_s
        # The temporary manual GUI cannot execute SWITCH. Enable it explicitly
        # when the shared engine is connected, rather than crashing during replay.
        self.supported_actions = frozenset(supported_actions)
        self.solving = False
        self.algorithm = None
        self.result = None
        self.start_state = None
        self._game_map = None
        self._cancel_requested = False
        self._restore = None
        self._pending_step = False
        self.panel_open = False
        self._panel_progress = 0.0
        self._panel_velocity = 0.0

    # ----- state -----------------------------------------------------------
    @property
    def busy(self):
        """True while manual movement must be blocked."""
        return self.solving or self.replay.playing or self._pending_step

    def reset(self):
        """Call on restart / level change: drop any running solve and replay."""
        self.worker.discard()
        self.solving = False
        self.algorithm = None
        self.result = None
        self.start_state = None
        self._game_map = None
        self._cancel_requested = False
        self._restore = None
        self._pending_step = False
        self.replay.load([])

    def on_manual_move(self):
        """A manual move makes the loaded solution out of date."""
        self.replay.load([])
        self._pending_step = False
        self.start_state = None
        self._restore = None

    def take_restore_state(self):
        state, self._restore = self._restore, None
        return state

    # ----- commands --------------------------------------------------------
    def can_run(self, command, ready=True):
        if command in ALGORITHMS:
            return ready
        if command == "CANCEL":
            return self.solving and not self._cancel_requested
        if command == "SPEED":
            return True
        if self.solving or not self.replay.actions:
            return False
        if command == "STEP":
            return not self.replay.done and not self._pending_step
        if command == "PLAY":
            return not self.replay.done or ready
        return command == "STOP" and self.start_state is not None

    def run(self, command, game_map, state, ready=True):
        if not self.can_run(command, ready):
            return
        if command in ALGORITHMS:
            self.reset()
            self.algorithm = command
            self.solving = True
            self.start_state = copy.deepcopy(state)
            self._game_map = copy.deepcopy(game_map)
            self._restore = copy.deepcopy(state)  # lets the game clear old messages
            self.worker.start(game_map, state, command, self.timeout_s)
        elif command == "CANCEL" and self.solving:
            self._cancel_requested = True
            self.worker.cancel()
        elif command == "PLAY":
            self._pending_step = False
            if self.replay.done and self.replay.actions and self.start_state:
                self.replay.load(self.replay.actions)  # replay again from start
                self._restore = copy.deepcopy(self.start_state)
            self.replay.toggle()
        elif command == "STEP":
            self.replay.pause()
            self._pending_step = True
        elif command == "STOP" and self.start_state is not None:
            self.replay.load(self.replay.actions)
            self._pending_step = False
            self._restore = copy.deepcopy(self.start_state)
        elif command == "SPEED":
            self.replay.cycle_speed()

    def handle_key(self, key, game_map, state, ready=True):
        command = KEYS.get(key)
        if command is None:
            return False
        self.run(command, game_map, state, ready)
        return True

    def handle_click(self, pos, screen_size, game_map, state, ready=True):
        if self._toggle_rect(*screen_size).collidepoint(pos):
            self.panel_open = not self.panel_open
            return True
        if self._panel_progress <= 0.0:
            return False
        # Moving controls cannot be clicked accidentally while the drawer slides.
        if not self.panel_open or self._panel_progress < 1.0:
            return self._panel_rect(*screen_size).collidepoint(pos)
        for command, _, rect in self._layout(*screen_size):
            if rect.collidepoint(pos):
                self.run(command, game_map, state, ready)
                return True
        return self._panel_rect(*screen_size).collidepoint(pos)

    def update(self, dt, ready):
        """Collect finished results; return the next replay action, if any."""
        self._update_panel(max(0.0, dt))
        result = self.worker.poll()
        if result is not None and self.solving:
            try:
                result = validate_result(result, self._game_map, self.start_state,
                                         self.algorithm, self.timeout_s,
                                         self.supported_actions)
            except (ValueError, TypeError, OverflowError, RecursionError) as error:
                result = make_result(self._game_map, self.start_state, self.algorithm,
                                     self.timeout_s, "ERROR", f"Invalid solver result: {error}")
            if self._cancel_requested and result["status"] != "CANCELLED":
                cancelled = make_result(self._game_map, self.start_state, self.algorithm,
                                        self.timeout_s, "CANCELLED")
                for name in ("search_time_s", "peak_memory_bytes", "expanded_nodes"):
                    cancelled["metrics"][name] = result["metrics"][name]
                result = cancelled
            self.solving = False
            self._cancel_requested = False
            self.result = result
            if result.get("status") == "SOLVED":
                self.replay.load(result.get("actions") or [])
                self.replay.play()
        if self._pending_step:
            if not ready:
                return None
            self._pending_step = False
            return self.replay.step()
        return self.replay.update(dt, ready)

    # ----- drawing ---------------------------------------------------------
    def _update_panel(self, dt):
        """Exact critically damped spring: preserve velocity on direction changes.

        Solving analytically keeps the same motion at different frame rates,
        including a delayed frame, without overshoot or integration substeps.
        """
        target = float(self.panel_open)
        offset = self._panel_progress - target
        rate = PANEL_SPRING_RATE
        momentum = self._panel_velocity + rate * offset
        decay = math.exp(-rate * dt)
        self._panel_progress = target + (offset + momentum * dt) * decay
        self._panel_velocity = (self._panel_velocity - rate * momentum * dt) * decay
        # Finish only once the remaining travel and speed are imperceptible.
        if (abs(self._panel_progress - target) < 0.0004
                and abs(self._panel_velocity) < 0.002):
            self._panel_progress = target
            self._panel_velocity = 0.0

    def _panel_rect(self, w, h):
        return pygame.Rect(w - round(PANEL_W * self._panel_progress),
                           64, PANEL_W, 470)

    def _toggle_rect(self, w, h):
        right = self._panel_rect(w, h).left
        return pygame.Rect(right - TOGGLE_W, h // 4 - TOGGLE_H // 2,
                           TOGGLE_W, TOGGLE_H)

    def _layout(self, w, h):
        panel = self._panel_rect(w, h)
        x, y, half = panel.x + 10, panel.y + 34, (PANEL_W - 30) // 2
        buttons = []
        for i, algo in enumerate(ALGORITHMS):
            rect = pygame.Rect(x + (i % 2) * (half + 10), y + (i // 2) * 40, half, 34)
            buttons.append((algo, ALGO_LABELS[algo], rect))
        buttons.append(("CANCEL", "C  Cancel", pygame.Rect(x, y + 80, PANEL_W - 20, 32)))
        y = panel.bottom - 84
        third = (PANEL_W - 40) // 3
        play_label = "Pause" if self.replay.playing else "Play"
        for i, (cmd, label) in enumerate((("PLAY", play_label), ("STEP", "Step"),
                                          ("STOP", "Stop"))):
            buttons.append((cmd, label, pygame.Rect(x + i * (third + 10), y, third, 34)))
        buttons.append(("SPEED", f"F  Speed x{self.replay.speed:g}",
                        pygame.Rect(x, y + 42, PANEL_W - 20, 32)))
        return buttons

    def draw(self, screen, font):
        w, h = screen.get_size()
        mouse = pygame.mouse.get_pos()
        toggle = self._toggle_rect(w, h)
        pygame.draw.rect(screen, (91, 123, 168) if toggle.collidepoint(mouse)
                         else (63, 83, 115), toggle,
                         border_top_left_radius=9, border_bottom_left_radius=9)
        label = font.render(">>" if self.panel_open else "<<", True, (240, 243, 250))
        screen.blit(label, label.get_rect(center=toggle.center))
        if self._panel_progress <= 0.0:
            return
        panel = self._panel_rect(w, h)
        box = pygame.Surface(panel.size, pygame.SRCALPHA)
        box.fill((14, 20, 32, 215))
        screen.blit(box, panel.topleft)
        pygame.draw.rect(screen, (70, 90, 125), panel, 1, border_radius=8)
        self._text(screen, font, "AUTO SOLVER", (panel.x + 12, panel.y + 9))

        for command, label, rect in self._layout(w, h):
            active = (command == self.algorithm and self.solving) or \
                     (command == "PLAY" and self.replay.playing)
            disabled = not self.can_run(command)
            color = (60, 70, 85) if disabled else \
                (95, 135, 200) if active or rect.collidepoint(mouse) else (55, 78, 112)
            pygame.draw.rect(screen, color, rect, border_radius=7)
            surface = font.render(label, True, (150, 155, 165) if disabled else (240, 243, 250))
            screen.blit(surface, surface.get_rect(center=rect.center))

        y = panel.y + 160
        for label, value, color in self._stat_lines():
            self._text(screen, font, label, (panel.x + 12, y), (165, 175, 195))
            surface = font.render(value, True, color)
            screen.blit(surface, (panel.right - 12 - surface.get_width(), y))
            y += 25

    def _stat_lines(self):
        white = (240, 243, 250)
        if self.solving:
            status = "CANCELLING" if self._cancel_requested else "SOLVING"
        elif self.result:
            status = self.result.get("status", "ERROR")
        else:
            status = "-"
        metrics = {} if self.solving else ((self.result or {}).get("metrics") or {})
        algo = "A*" if self.algorithm == "ASTAR" else (self.algorithm or "-")
        time_s = metrics.get("search_time_s")
        lines = [
            ("Algorithm", algo, white),
            ("Status", status, STATUS_COLORS.get(status, white)),
            ("Time", _fmt(time_s if time_s is None else time_s * 1000, "{:.1f} ms"), white),
            ("Peak memory", _format_bytes(metrics.get("peak_memory_bytes")), white),
            ("Expanded", _fmt(metrics.get("expanded_nodes")), white),
            ("Length", _fmt(metrics.get("solution_length")), white),
            ("Cost", _fmt(metrics.get("solution_cost")), white),
            ("Replay", f"{self.replay.index}/{len(self.replay.actions)}"
             if self.replay.actions else "-", white),
        ]
        error = (self.result or {}).get("error")
        if error and not self.solving:
            lines.append(("Error", str(error)[:22], STATUS_COLORS["ERROR"]))
        return lines

    @staticmethod
    def _text(screen, font, value, topleft, color=(240, 243, 250)):
        screen.blit(font.render(str(value), True, color), topleft)
