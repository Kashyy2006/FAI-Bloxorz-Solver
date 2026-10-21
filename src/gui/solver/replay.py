"""Timed playback of a solution action list (play / pause / step / speed)."""

BASE_DELAY_S = 0.45
SPEEDS = (0.5, 1.0, 2.0, 4.0)


class Replay:
    def __init__(self):
        self.speed_index = 1
        self.load([])

    def load(self, actions):
        self.actions = list(actions or [])
        self.index = 0
        self.playing = False
        self._timer = 0.0

    @property
    def speed(self):
        return SPEEDS[self.speed_index]

    @property
    def done(self):
        return self.index >= len(self.actions)

    def cycle_speed(self):
        self.speed_index = (self.speed_index + 1) % len(SPEEDS)

    def play(self):
        if not self.done:
            self.playing = True
            self._timer = BASE_DELAY_S / self.speed  # first step at every speed

    def pause(self):
        self.playing = False

    def toggle(self):
        if self.playing:
            self.pause()
        else:
            self.play()

    def step(self):
        """Pause and return the next action (or None at the end)."""
        self.pause()
        return self._next()

    def update(self, dt, ready):
        """Return the next action when it is due and the game is ready for it."""
        if not self.playing:
            return None
        # Count wall time during movement too: delay is start-to-start, not extra
        # waiting after every animation. Cap it to avoid bursts after a blocked frame.
        self._timer = min(BASE_DELAY_S / self.speed, self._timer + max(0.0, dt))
        if not ready or self._timer < BASE_DELAY_S / self.speed:
            return None
        self._timer = 0.0
        return self._next()

    def _next(self):
        if self.done:
            return None
        action = self.actions[self.index]
        self.index += 1
        if self.done:
            self.playing = False
        return action
