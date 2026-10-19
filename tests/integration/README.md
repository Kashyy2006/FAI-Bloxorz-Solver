# tests/integration

**Lưu gì / làm gì:** Kiểm thử engine-GUI-solver, chạy nền, hủy, đọc kết quả và phát lại.

**Phụ trách:** Thành viên 3 phối hợp thành viên 2.

## Phạm vi hiện tại

- `test_advanced_shared_engine.py`: kiểm thử tích hợp `src.solvers.solve.solve`
  và các hàm binding (`run_bfs`, `run_dfs`, `run_ucs`, `run_astar`) cho cả bốn
  thuật toán trên map cơ bản và nâng cao (cầu, công tắc, fragile, split/merge),
  đối chiếu chi phí với `step_cost` của engine, kiểm tra hủy/timeout/vô nghiệm
  và đồng bộ trạng thái GUI-engine.
- `test_game_launch.py`: khởi chạy điểm vào game ở tiến trình riêng bằng SDL dummy.
- `test_solver_gui_backend.py`: solver tạm, replay và worker cơ bản.
- `test_solver_controller.py`: Step liên tiếp, Play/Pause/Stop, reset, thao tác
  trong animation, dữ liệu sai, render lỗi headless; chạy cả bốn solver thật từ
  trạng thái giữa ván (gồm cấu hình cầu và khối tách `SPLIT`/`SWITCH`) và phát
  lại bằng `_move` thật của GUI tới đích; kiểm tra vòng lặp `game.main()` với
  sự kiện chọn màn, Solve và Pause giữa animation.
- `test_solver_worker.py`: thay tác vụ không chạy chồng, chỉ giữ yêu cầu mới nhất,
  hủy tác vụ đang chạy/đang chờ, kết quả cũ, snapshot map/state, lỗi solver.
- `test_solver_result.py`: JSON/schema, danh tính lượt giải, trạng thái cầu,
  kiểu/giá trị metrics, độ dài/chi phí lời giải, actions và envelope `ERROR` có
  trường `null` khi chưa xác thực.

Chạy toàn bộ kiểm thử từ gốc project:

```console
python -m unittest discover -s tests -t . -v
```

