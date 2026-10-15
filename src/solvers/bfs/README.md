# src/solvers/bfs

**Lưu gì / làm gì:** Thuật toán BFS, chống lặp và xuất lời giải.

**Phụ trách:** Thành viên 4.

## Lõi BFS độc lập

Đã triển khai lõi tìm kiếm và 11 test trên đồ thị giả hữu hạn, không cần engine
hoặc thư viện ngoài. Dùng deque FIFO; membership trong `parent` là visited,
đánh dấu ngay khi enqueue. Giữ nguyên thứ tự successors, kiểm tra goal khi lấy
nút ra và trước mở rộng. Dùng lại `reconstruct_actions` của common.

### Cách gọi nội bộ

Chạy Python từ gốc repo `D:/FAI_lab`:

```python
from src.solvers.bfs.solver import _search

actions, solution_cost, expanded_nodes = _search(
    game_map,
    start_state,
    state_key=state_key,
    is_goal=is_goal,
    successors=successors,
)
```

Đây là ví dụ cách nối API, cần cung cấp map/state và ba callable:

- `state_key(state)` trả khóa hashable `(mode, cells, active, bridges)`.
- `is_goal(game_map, state)` xác định đích.
- `successors(game_map, state)` trả danh sách theo thứ tự engine; mỗi phần tử
  có `action`, `state`, `cost`. Chỉ đưa bước hợp lệ, chi phí nguyên ≥ 1.

Map/state phải hợp lệ, bất biến trong lượt tìm kiếm và đồ thị phải hữu hạn.
Hàm không sửa đầu vào và không nạp map hoặc tự triển khai luật game.

Kết quả là tuple `(actions, solution_cost, expanded_nodes)`:

- Có lời giải: list actions, tổng chi phí của đường đã chọn và số mở rộng.
- Start đã thắng: `([], 0, 0)`, không khởi tạo frontier hoặc gọi successors.
- Cạn frontier: `(None, None, expanded_nodes)`, khác với lời giải rỗng.

BFS tối ưu **số hành động**, kể cả `SWITCH`; chi phí chỉ để báo cáo.
Không đổi parent khi gặp lại key qua đường rẻ hơn. `expanded_nodes` đếm số
lần gọi successors, không tính goal. Bộ nhớ O(V), thời gian trung bình O(V+E)
theo số state key/cạnh; không lưu bản sao toàn bộ đường đi cho mỗi nút.

### Kiểm thử

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_bfs.py' -v
python -m unittest discover -s tests/solvers -p 'test_*.py' -v
```

Đã chạy đạt **11 test BFS + 13 test common = 24 test**, không skip.
Bao gồm đường ngắn, phá hòa, đường ít bước khác đường rẻ nhất, diamond/chu
trình/self-loop, vô nghiệm, start đã thắng, cầu, active/SWITCH, các tư thế,
input bất biến/chạy lại và lỗi từ cả ba callable. Ca diamond có queue spy để
xác nhận enqueue mỗi key một lần, kể cả hai object khác nhau cùng full key.

### Giới hạn và tích hợp

`_search` là lõi nội bộ; chưa có API công khai `solve(...)`, `SolverResult`,
validation snapshot, timeout/hủy hoặc đo thời gian/bộ nhớ. Ngoại lệ callback
được truyền ra ngoài, không biến thành kết luận vô nghiệm.

Khi bổ sung kiểm soát chạy, mở rộng chính vòng BFS để kiểm tra CANCELLED trước
TIMEOUT mỗi vòng và trong xử lý successors; thêm đo/validation/ERROR và đóng
gói qua common. Không tạo vòng BFS thứ hai. Tích hợp ba hàm engine thật,
metadata map và replay lời giải sau khi API engine sẵn sàng. Chưa kiểm tra
luật Bloxorz, map thật hoặc GUI.
