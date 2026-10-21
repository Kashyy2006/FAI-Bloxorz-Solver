# Chi phí dùng chung — TV5 phối hợp TV1

Hàm chuẩn được chọn: `calculate_step_cost(game_map, current_state, next_state, action)`
trong `calc.py`. API `src.engine.rules.step_cost(game_map, state, action, next_state)`
chỉ chuyển tiếp sang hàm này. Cả bốn solver cộng `Successor.cost` đúng một lần.

Công thức: `1 + 2*F + T`, tính từ các ô trong `next_state.cells` không có trong
`current_state.cells`. F đếm fragile mới chiếm; T đếm soft mới chiếm và heavy mới
chiếm khi trạng thái cuối đứng thẳng. SWITCH có giá 1; split không cộng phụ phí.
Đây là quy ước chi phí sau khi hoàn tất chuyển trạng thái, khác với sự kiện kích
hoạt công tắc trước teleport/nhập của engine.

Đọc loại ô bằng `GameMap.tile_at()`. Không dùng các thuộc tính tự đặt như
fragile_tiles/soft_switches/heavy_switches hoặc giá trị mặc định che lỗi dữ liệu.
Cost là chi phí một bước; heuristic là cận dưới chi phí còn lại.

`heuristic_name()` chọn và trả tên chiến lược dùng trong JSON: map động dùng
`goal_indicator_v1`; map tĩnh nhỏ dùng `reverse_bfs_manhattan_fallback_v1` (khoảng
cách số bước, fallback Manhattan cho tư thế không nối tới goal); map tĩnh lớn
hơn 1000 tư thế dùng `manhattan_orientation_v1`. Bắt đầu ở SPLIT giữ goal indicator
trong cả lượt tìm kiếm, kể cả sau khi nhập khối.

### Tiền xử lý Reverse BFS

A* dựng đồ thị đảo một lần cho mỗi lượt giải map tĩnh nhỏ, sau khi bắt đầu runtime.
`search_time_s` và `peak_memory_bytes` bao gồm tiền xử lý; `expanded_nodes` chỉ đếm
nút mở rộng của A*, không cộng các tư thế duyệt khi dựng heuristic. Kiểm tra hủy/
timeout trong các vòng dựng đồ thị và BFS ngược; dừng trước tìm kiếm vẫn giữ số đo.
Không dùng cache từ lượt trước trong solver/benchmark. Cache của helper tra cứu
heuristic độc lập không được dùng cho các lượt tìm kiếm có đo. Map động và map tĩnh
lớn không dựng Reverse BFS. Start đã thắng giữ fast path không tiền xử lý.
