import math

from .settings import TILE_HEIGHT, TILE_WIDTH


class Camera:
    def __init__(self, width, height, screen_width, screen_height):
        self.width = width
        self.height = height
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.angle = 0.0
        self.start_angle = 0.0
        self.target_angle = 0.0
        self.duration = 0.5
        self.elapsed = 0.0
        self.rotating = False
        self.zoom = 1.0
        self.min_zoom = 0.4
        self.max_zoom = 2.5
        self.offset_x = 0.0
        self.offset_y = 0.0

    def rotate(self, direction):
        if self.rotating:
            return
        self.start_angle = self.angle
        self.target_angle = self.angle + direction * 90
        self.elapsed = 0.0
        self.rotating = True

    def update(self, dt):
        if not self.rotating:
            return
        self.elapsed += dt
        t = min(self.elapsed / self.duration, 1.0)
        smooth_t = t * t * (3 - 2 * t)
        self.angle = self.start_angle + (self.target_angle - self.start_angle) * smooth_t
        if t >= 1.0:
            self.angle = self.target_angle
            self.rotating = False

    def project(self, row, col):
        radians = math.radians(self.angle)
        dx = col - (self.width - 1) / 2
        dy = row - (self.height - 1) / 2
        rotated_x = dx * math.cos(radians) - dy * math.sin(radians)
        rotated_y = dx * math.sin(radians) + dy * math.cos(radians)
        scale = self.zoom
        x = self.screen_width / 2 + self.offset_x + (rotated_x - rotated_y) * TILE_WIDTH * scale / 2
        y = self.screen_height / 2 + self.offset_y + (rotated_x + rotated_y) * TILE_HEIGHT * scale / 2
        return x, y

    def scale(self, value):
        return value * self.zoom

    def resize(self, width, height):
        self.screen_width = max(1, width)
        self.screen_height = max(1, height)

    def change_zoom(self, steps):
        self.zoom = min(self.max_zoom, max(self.min_zoom, self.zoom * (1.1 ** steps)))

    def move(self, dx, dy):
        self.offset_x += dx
        self.offset_y += dy

    def reset(self):
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
