# Giao diện chơi thủ công

Chạy từ thư mục gốc của dự án bằng lệnh `python -m src.gui.manual.game`.

Cũng có thể chạy trực tiếp `python src/gui/manual/game.py` hoặc dùng nút Run
trong IDE. Khi chạy từ thư mục khác, truyền đường dẫn tuyệt đối tới `game.py`;
map và nhạc vẫn được tìm theo thư mục dự án.

- Menu chính có các nút Chơi, Cài đặt và Thoát.
- Chọn **Chơi** để mở danh sách màn. Danh sách được đọc từ các tệp JSON trong `data/maps/`.
- Trong màn chơi: dùng phím mũi tên hoặc WASD để di chuyển; Q/E xoay bàn chơi mượt; R chơi lại; L quay về danh sách màn; Esc quay về menu. Khối có hoạt ảnh khi lăn.
- Giữ nút chuột giữa và kéo để di chuyển bàn chơi; dùng con lăn để phóng to hoặc thu nhỏ.
- Cài đặt cho phép chỉnh âm lượng, độ sáng và chuyển giữa chế độ cửa sổ/toàn màn hình.
- Game tự phát lặp tệp `.mp3`, `.ogg` hoặc `.wav` đầu tiên trong `data/bgm/`. Thanh âm lượng trong Cài đặt điều chỉnh âm lượng nhạc.

Giao diện hiện dùng engine chung cho map, di chuyển, fragile, cầu, công tắc và tách/nhập khối.
Dùng **Tab** đổi khối nhỏ đang điều khiển; vòng trắng đánh dấu khối active.
Cầu đóng được ẩn khỏi mặt sàn. Solver dùng src/solvers/solve.py và replay lại qua engine.
Hai map advanced_bridge_01 và advanced_split_01 phục vụ kiểm tra cơ chế nâng cao.

**Phụ trách:** Thành viên 2 (giao diện chơi thủ công).
