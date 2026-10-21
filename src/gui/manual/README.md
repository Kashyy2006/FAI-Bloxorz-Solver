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

GUI tải và kiểm tra map bằng validator của `src/engine`, đồng thời dùng `initial_state` và `transition` cho di chuyển, thắng và thua. Bản engine hiện tại chỉ nhận `void`, `floor`, `goal`, `fragile` và khối nguyên; map có cầu, công tắc hoặc cơ chế tách khối sẽ bị từ chối cho đến khi engine hỗ trợ đầy đủ.

Khi xoay camera bằng Q/E, các phím mũi tên và WASD được đổi hướng theo góc nhìn.

**Phụ trách:** Thành viên 2 (giao diện chơi thủ công).

## Hoạt ảnh rơi và cầu

- Khi khối nằm mất một ô đỡ, khối chúi về phía ô trống rồi rơi/mờ dần. Khối đứng mất ô đỡ rơi xuống trước khi hiện Game Over.
- Cầu nâng/hạ trong 0,38 giây theo events BRIDGE_CHANGED của engine; cầu đóng biến mất khỏi sàn.
- Trong khi cầu chuyển động, tạm chặn bước đi/phát lại tiếp theo; Restart và đổi màn đặt lại trạng thái hiển thị.
- animations.py chỉ quản lý thời gian/độ mở hiển thị; luật game vẫn do engine quyết định.

- Split có hoạt ảnh riêng 0,85 giây: lăn lên công tắc, tách hai khối nhỏ, vòng sáng và di chuyển đến destinations của engine.
- Khối nhỏ mất ô đỡ di chuyển tới đúng ô rơi rồi nghiêng/rơi/mờ dần; khối còn được đỡ vẫn hiển thị sau Game Over. Khối nhỏ di chuyển và nhập lại cũng được nội suy vị trí.

### Reset và lỗi solver

- Đổi màn hoặc về menu hủy hoạt ảnh/replay cũ; Restart và phím R dùng cùng reset.
- Lệnh INVALID giữ nguyên lời giải đang nạp. Di chuyển thủ công hợp lệ làm lời giải cũ hết hiệu lực.
- Cửa sổ có kích thước tối thiểu 900 × 600 để giữ các nút trong vùng hiển thị.
- Nhấn F1 hoặc nút **Error details** trong bảng solver để xem toàn bộ lỗi, cuộn bằng con lăn và đóng bằng F1/click.

### Replay, nhận diện ô và map lỗi

- Tốc độ 0.5x/1x/2x/4x áp dụng cả khoảng cách giữa các bước và hoạt ảnh lăn,
  cầu, tách khối, rơi trong replay. Chơi thủ công giữ tốc độ bình thường.
- Ô đặc biệt có chữ mờ GOAL/FRAGILE/SOFT/HEAVY/SPLIT/BRIDGE. Hover chỉ hiện tên loại ô
  và tọa độ.
  Cầu đóng ẩn chữ BRIDGE; hover chỉ hiện tên Bridge và tọa độ. Không tạo ô đỡ mới trong engine.
- Trang chọn màn hiện số map lỗi. F2 hoặc nút Invalid maps mở chi tiết tên file
  và nguyên nhân; cuộn để đọc, F2/Esc/click để đóng. Sửa file rồi nhấn F5 để nạp lại.
  File lỗi được bỏ qua, map hợp lệ vẫn chơi được.
