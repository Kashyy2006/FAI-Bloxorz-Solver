# Chi phí dùng chung — TV5 phối hợp TV1

Hàm chuẩn: src.engine.rules.step_cost(game_map, state, action, next_state).
calculate_step_cost(game_map, current_state, next_state, action) giữ thứ tự tham số
cũ và chỉ gọi hàm chuẩn. UCS/A* cộng Successor.cost do engine trả, không cộng hai lần.

Công thức: `1 + 2*F + T`. F là fragile mới chiếm; T là soft/heavy vừa kích hoạt,
được tính qua cùng logic nhấn công tắc của transition. SWITCH có giá 1.

Không đọc fragile_tiles/soft_switches/heavy_switches tự đặt trên GameMap; map thật
lưu grid qua tile_at() và các khai báo switches. Không dùng getattr mặc định tập
rỗng để che lỗi cấu trúc dữ liệu. Cost khác heuristic: h ước lượng phần còn lại,
trong khi cost là chi phí của một bước đã đi.

Các kiểm thử engine nâng cao kiểm tra chi phí kích hoạt và fragile với map thật;
tests/solvers/test_TV5_ucs.py kiểm tra API tương thích của TV5.
