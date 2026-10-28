"""Exercise both entry points in fresh processes with no visible window."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class GameLaunchTest(unittest.TestCase):
    def launch(self, entry, cwd, *args):
        env = os.environ.copy()
        env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
                   PYGAME_HIDE_SUPPORT_PROMPT="1", PYTHONDONTWRITEBYTECODE="1")
        env.pop("PYTHONPATH", None)
        # Queue Quit so the real entry point initializes, renders once and exits.
        code = (
            "import pygame, runpy, sys; "
            "pygame.event.get = lambda: [pygame.event.Event(pygame.QUIT)]; "
            + entry
        )
        result = subprocess.run([sys.executable, "-c", code, *args], cwd=cwd,
                                env=env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_direct_file_from_another_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            self.launch("runpy.run_path(sys.argv[1], run_name='__main__')", directory,
                        str(ROOT / "src/gui/manual/game.py"))

    def test_module_from_project_root(self):
        self.launch("runpy.run_module('src.gui.manual.game', run_name='__main__')", ROOT)
