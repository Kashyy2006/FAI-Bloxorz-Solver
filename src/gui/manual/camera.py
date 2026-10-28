import math

from .settings import TILE_HEIGHT, TILE_WIDTH


# Quản lý góc nhìn, phép chiếu và thao tác camera trên bản đồ.
class Camera:
    def __init__(self, width, height, screen_width, screen_height):
        # Khởi tạo camera theo kích thước bản đồ và cửa sổ.
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
        # Bắt đầu xoay camera 90 độ theo hướng chỉ định.
        if self.rotating:
            return
        self.start_angle = self.angle
        self.target_angle = self.angle + direction * 90
        self.elapsed = 0.0
        self.rotating = True

    def update(self, dt):
        # Cập nhật tiến trình xoay camera theo thời gian.
        if not self.rotating:
            return
        self.elapsed += dt
        # Chuẩn hóa thời gian xoay về 0..1 rồi làm mượt để camera tăng/giảm tốc êm.
        t = min(self.elapsed / self.duration, 1.0)
        smooth_t = t * t * (3 - 2 * t)
        self.angle = self.start_angle + (self.target_angle - self.start_angle) * smooth_t
        if t >= 1.0:
            self.angle = self.target_angle
            self.rotating = False

    def project(self, row, col):
        # Chuyển tọa độ ô bản đồ thành tọa độ trên màn hình.
        radians = math.radians(self.angle)
        # Đưa ô về tọa độ tương đối quanh tâm map để map xoay tại chỗ.
        dx = col - (self.width - 1) / 2
        dy = row - (self.height - 1) / 2
        # Xoay tọa độ phẳng theo góc camera.
        rotated_x = dx * math.cos(radians) - dy * math.sin(radians)
        rotated_y = dx * math.sin(radians) + dy * math.cos(radians)
        scale = self.zoom
        # Chiếu sang mặt phẳng isometric rồi áp dụng tâm màn hình, pan và zoom.
        x = self.screen_width / 2 + self.offset_x + (rotated_x - rotated_y) * TILE_WIDTH * scale / 2
        y = self.screen_height / 2 + self.offset_y + (rotated_x + rotated_y) * TILE_HEIGHT * scale / 2
        return x, y

    def scale(self, value):
        # Điều chỉnh kích thước theo mức thu phóng hiện tại.
        return value * self.zoom

    def resize(self, width, height):
        # Cập nhật kích thước vùng hiển thị của camera.
        self.screen_width = max(1, width)
        self.screen_height = max(1, height)

    def change_zoom(self, steps):
        # Phóng to hoặc thu nhỏ camera theo số nấc cuộn.
        self.zoom = min(self.max_zoom, max(self.min_zoom, self.zoom * (1.1 ** steps)))

    def move(self, dx, dy):
        # Dịch chuyển góc nhìn theo độ lệch màn hình.
        self.offset_x += dx
        self.offset_y += dy

    def reset(self):
        # Đưa mức thu phóng và vị trí camera về mặc định.
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
