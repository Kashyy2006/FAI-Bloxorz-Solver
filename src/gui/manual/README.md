# Giao diện chơi thủ công

Chạy từ thư mục gốc của dự án bằng lệnh `python -m src.gui.manual.game`.

- Menu chính có các nút Chơi, Cài đặt và Thoát.
- Chọn **Chơi** để mở danh sách màn. Danh sách được đọc từ các tệp JSON trong `data/maps/`.
- Trong màn chơi: dùng phím mũi tên hoặc WASD để di chuyển; Q/E xoay bàn chơi mượt; R chơi lại; L quay về danh sách màn; Esc quay về menu. Khối có hoạt ảnh khi lăn.
- Giữ nút chuột giữa và kéo để di chuyển bàn chơi; dùng con lăn để phóng to hoặc thu nhỏ.
- Cài đặt cho phép chỉnh âm lượng, độ sáng và chuyển giữa chế độ cửa sổ/toàn màn hình.
- Game tự phát lặp tệp `.mp3`, `.ogg` hoặc `.wav` đầu tiên trong `data/bgm/`. Thanh âm lượng trong Cài đặt điều chỉnh âm lượng nhạc.

Hiện giao diện dùng phần xử lý di chuyển tạm thời vì API engine dùng chung chưa được triển khai. Phần này hỗ trợ di chuyển cơ bản, rơi và xác định ô đích; luật của các ô đặc biệt sẽ được nối với engine khi engine sẵn sàng.

**Phụ trách:** Thành viên 2 (giao diện chơi thủ công).
