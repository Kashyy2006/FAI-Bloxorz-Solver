# src/solvers

**Lưu gì / làm gì:** Các thuật toán tìm kiếm tự cài đặt; dùng chung luật engine và định dạng kết quả.

**Phụ trách:** Thành viên 4 và 5.

## Điểm gọi tích hợp

`from src.solvers.solve import solve`

`solve(game_map, start_state, algorithm, timeout_s=60.0, cancel_event=None)`
nhận GameMap/State hoặc map JSON/snapshot, trả dict theo contract. Các tên
thuật toán là BFS, DFS, UCS, ASTAR; tất cả dùng src.engine.successors.
UCS và A* có kernel riêng, dùng cùng runtime/JSON boundary. A* ghi đúng tên heuristic đã chọn theo map. Backend
GUI mặc định gọi điểm này; placeholder_solver chỉ còn là bản tạm lịch sử.
