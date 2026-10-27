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

## Heuristic hiện tại (27/10/2026)

`heuristic_name(game_map, split=False)` chọn một chiến lược cho cả lượt tìm kiếm:

1. Map có ô split/teleport, hoặc snapshot bắt đầu ở SPLIT: `goal_indicator_v1`
   (0 tại goal, 1 khi chưa thắng). Giữ chiến lược này cả sau khi nhập khối.
2. Map có cầu/công tắc nhưng không có split: `manhattan_orientation_v1`.
3. Map tĩnh không có cầu/công tắc/split, tối đa 1000 tư thế nguyên khối theo
   cách đếm của chương trình: `reverse_bfs_manhattan_fallback_v1`.
4. Map tĩnh lớn hơn ngưỡng: `manhattan_orientation_v1`.

Manhattan dùng `d = min(abs(r-r_goal) + abs(c-c_goal))` trên các ô khối chiếm,
`h = ceil(d/2)`. Khi khối lớn nằm phủ goal (`d=0`) thì dùng `h=1`, không còn
hiệu chỉnh 4 như trước. Goal đứng có h=0. Cận này nhất quán với các bước lăn
không teleport có chi phí >= 1; map split/teleport dùng goal indicator.

Reverse BFS dùng cạnh đảo của đồ thị tư thế hợp lệ trên map tĩnh, giữ luật fragile,
đếm mỗi cạnh một hành động. Nếu không có khoảng cách ngược thì fallback Manhattan;
không phải đợi gặp cầu mới fallback. Cầu/công tắc không teleport được xử lý ngay
bằng Manhattan, không dựng đồ thị Reverse BFS tĩnh.

| Chiến lược chính | Bộ benchmark 18 map | Tất cả 20 map trong GUI |
| --- | ---: | ---: |
| Reverse BFS + fallback Manhattan | 6 | 6 |
| Manhattan | 8 | 9 |
| Goal indicator | 4 | 5 |

Tên JSON `manhattan_orientation_v1` được giữ để tương thích. Khi so sánh kết quả,
phải đối chiếu commit và hash nguồn: cùng tên này trước commit `486a584` có thể
còn dùng hiệu chỉnh 4. Kết quả A* cũ không đại diện cho công thức/chọn chiến lược mới.

### Tiền xử lý Reverse BFS

A* dựng đồ thị đảo một lần cho mỗi lượt giải map tĩnh nhỏ, sau khi bắt đầu runtime.
`search_time_s` và `peak_memory_bytes` bao gồm tiền xử lý; `expanded_nodes` chỉ đếm
nút mở rộng của A*, không cộng các tư thế duyệt khi dựng heuristic. Kiểm tra hủy/
timeout trong các vòng dựng đồ thị và BFS ngược; dừng trước tìm kiếm vẫn giữ số đo.
Không dùng cache từ lượt trước trong solver/benchmark. Cache của helper tra cứu
heuristic độc lập không được dùng cho các lượt tìm kiếm có đo. Map động và map tĩnh
lớn không dựng Reverse BFS. Start đã thắng giữ fast path không tiền xử lý.
