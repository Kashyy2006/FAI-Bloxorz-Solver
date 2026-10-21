# src/gui/solver

**Lưu gì / làm gì:** Nút chạy 4 solver từ trạng thái hiện tại, chạy nền, đọc JSON, thống kê, phát lại, tạm dừng và hủy.

**Phụ trách:** Thành viên 3.

## Vòng đời giải và phát lại

- Panel Solver mặc định thu gọn. Bấm `<<` sát cạnh phải, ở 1/4 chiều cao
  cửa sổ để mở; bấm `>>` để đóng. Thu gọn vẫn giữ kết quả và tiếp tục phát lại.
  Các phím tắt solver vẫn dùng được khi panel đang ẩn.
  Panel trượt theo chuyển động lò xo có giảm chấn, dừng mềm trong khoảng 0,6 giây
  và giữ quán tính khi bấm đảo chiều. Chuyển động nhất quán giữa các tốc độ khung
  hình. Nút đóng/mở luôn đi theo mép panel.

- `worker.py`: chụp riêng map/state; chỉ chạy một solver, giữ yêu cầu thay thế
  mới nhất. `poll()` được gọi mỗi frame để nhận kết quả và khởi động lượt đang chờ
  sau khi thread cũ đã thoát. Không chờ thread đang chạy trên luồng GUI.
- Cancel đặt event, chặn kết quả SOLVED về muộn và giữ thống kê đã đo. GUI hiển
  thị CANCELLING đến khi solver trả về. Solver phải kiểm tra `cancel_event` và
  `timeout_s`; Python thread không thể bị ép dừng an toàn nếu solver bỏ qua chúng.
  Reset/đổi màn bỏ kết quả và yêu cầu đang chờ. Thoát game cũng gửi yêu cầu hủy.
- `result.py`: nhận dict hoặc chuỗi JSON, kiểm tra schema trong
  `docs/contracts/solver.md`, snapshot của lượt giải và metrics trước khi phát lại.
  Kết quả lỗi được đổi thành ERROR đầy đủ để panel vẫn hiển thị an toàn.
- Step chỉ đặt một yêu cầu chờ; không lấy action/tăng chỉ số trước khi game sẵn
  sàng. Play thay yêu cầu Step đang chờ bằng phát liên tục; Stop xóa yêu cầu chờ
  và trở về snapshot ban đầu. Di chuyển thủ công làm mất hiệu lực replay đã nạp.
- Pause/Stop vẫn nhận được khi đang có animation; bắt đầu solve mới phải đợi
  animation kết thúc để snapshot khớp với trạng thái đang hiển thị.

`SolverController` mặc định gọi hàm điều phối `src.solvers.solve.solve` (hỗ trợ đủ
bốn thuật toán `BFS`, `DFS`, `UCS`, `ASTAR`) và bật đầy đủ 5 hành động
`("UP", "DOWN", "LEFT", "RIGHT", "SWITCH")` để giải và phát lại từ trạng thái
hiện tại (bao gồm cấu hình cầu và hai khối nhỏ khi tách). `placeholder_solver`
chỉ được giữ lại phục vụ kiểm thử hồi quy độc lập của worker/backend.

Kiểm thử toàn bộ: `python -m unittest discover -s tests -t . -v` (từ thư mục gốc).

