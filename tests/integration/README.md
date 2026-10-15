# tests/integration

**Lưu gì / làm gì:** Kiểm thử engine-GUI-solver, chạy nền, hủy, đọc kết quả và phát lại.

**Phụ trách:** Thành viên 3 phối hợp thành viên 2.

## Phạm vi hiện tại

- `test_solver_gui_backend.py`: solver tạm, replay và worker cơ bản.
- `test_solver_controller.py`: Step liên tiếp, Play/Pause/Stop, reset, thao tác
  trong animation, dữ liệu sai, render lỗi headless; chạy cả bốn solver tạm từ
  trạng thái đã di chuyển và phát lại bằng `_move` thật của GUI tới đích; kiểm tra
  vòng lặp `game.main()` với sự kiện chọn màn, Solve và Pause giữa animation.
- `test_solver_worker.py`: thay tác vụ không chạy chồng, chỉ giữ yêu cầu mới nhất,
  hủy tác vụ đang chạy/đang chờ, kết quả cũ, snapshot map/state, lỗi solver.
- `test_solver_result.py`: JSON/schema, danh tính lượt giải, trạng thái cầu,
  kiểu/giá trị metrics, độ dài/chi phí lời giải và actions.

Chạy từ gốc project: `python -m unittest discover -s tests -v`.

Engine và solver của thành viên 1/4/5 hiện chưa có triển khai trong source này.
Các test trên chưa chứng minh luật cầu/công tắc/tách khối hoặc tính đúng của
solver thật; cần bổ sung khi các module đó được bàn giao.
