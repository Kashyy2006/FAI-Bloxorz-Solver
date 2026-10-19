# src/solvers/bfs

**Lưu gì / làm gì:** Thuật toán BFS, chống lặp và xuất lời giải.

**Phụ trách:** Thành viên 4.

## Lõi BFS độc lập

Đã triển khai lõi tìm kiếm và runtime trên đồ thị giả hữu hạn, không cần engine
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

## Callable công khai

```python
from src.solvers.bfs.solver import solve_bfs

result = solve_bfs(
    game_map, start_state,
    map_id=map_id, bridge_ids=bridge_ids,
    state_key=state_key, is_goal=is_goal, successors=successors,
    validate_start_state=validate_start_state,
    timeout_s=60.0, cancel_event=cancel_event,
)
payload = result.to_dict()
```

Chữ ký đầy đủ:

```python
solve_bfs(
    game_map, start_state, *, map_id, bridge_ids,
    state_key, is_goal, successors, validate_start_state,
    timeout_s=60.0, cancel_event=None,
) -> SolverResult
```

Các keyword trước `timeout_s` đều bắt buộc; thiếu đối số gây `TypeError` tại
điểm gọi. Giá trị được truyền nhưng sai hoặc callback ném `Exception` trả
`SolverResult` với status `ERROR`. `_solve_bfs` được giữ làm alias tương thích.
Ví dụ trên cần được truyền các biến/callback tương ứng.
Không giả định thuộc tính của GameMap hay import engine chưa có. Validator
`validate_start_state(game_map, start_state)` phải ném lỗi có lý do khi snapshot
sai và trả bình thường khi hợp lệ; giá trị trả về không được sử dụng. Khi tích
hợp, cung cấp validator ngữ nghĩa của engine, không dùng callback no-op.
Bridge IDs là tuple các chuỗi không rỗng, duy nhất, theo thứ tự từ điển của
map, khớp số bridge bits của State; dùng `()` chỉ khi map thật không có cầu.
Callable kiểm tra kiểu/độ dài/thứ tự nhưng bên tích hợp phải bảo đảm đúng ID
của map; không thể suy ra metadata này từ các callback tùy ý.

Lớp bọc xác thực map ID/timeout/event/callback, gọi validator và chuyển snapshot
trước khi tìm kiếm; không sửa map/state hoặc lấy lại initial state. Kết quả có
SOLVED, UNSOLVABLE, TIMEOUT, CANCELLED, ERROR. Ngoại trừ SOLVED, actions/length/cost
đều None; ERROR có lý do và giữ số đo đã thu. Chỉ ERROR được có envelope field
chưa xác thực bằng None; JSON có 11 trường gốc, không đổi schema_version=1.

Start hợp lệ đã thắng trả SOLVED ngay sau validation, kể cả event đã set;
actions=[], length/cost/expanded/time/peak bằng 0, không tạo queue/tracer.
Khi tìm kiếm, hủy được ưu tiên trước timeout tại mỗi guard, gồm vòng xử lý
successors và trước kết luận cạn frontier. Deadline đạt đúng timeout là hết hạn.

`_search(..., runtime=None)` vẫn trả tuple như trước. Nếu tự truyền runtime,
truyền một `SearchRuntime` mới chưa start và luôn gọi `runtime.finish()` trong
finally; `_search` khởi động đo sau fast path và chốt timer trước dựng actions.
Lõi trực tiếp truyền lỗi callback ra ngoài; `solve_bfs` mới chuyển thành ERROR.
Xem [common](../common/README.md) về vòng đời đo và cleanup.

### Ví dụ fixture chạy độc lập

Chạy từ gốc repo. Đây là đồ thị xác định dùng kiểm tra cách gọi, không mô phỏng
luật cầu/split hoặc xác nhận lời giải Bloxorz:

```python
import json
from collections import namedtuple
from types import SimpleNamespace
from src.solvers.bfs.solver import solve_bfs

State = namedtuple("State", "mode cells active bridges")
start = State("SPLIT", ((1, 1), (3, 3)), 0, (True, False))
switched = start._replace(active=1)
goal = State("UPRIGHT", ((4, 4),), None, (True, False))
graph = {
    start: [SimpleNamespace(action="SWITCH", state=switched, cost=1)],
    switched: [SimpleNamespace(action="DOWN", state=goal, cost=3)],
    goal: [],
}

def validate_start_state(game_map, state):
    if state not in game_map:
        raise ValueError("snapshot is not in the fixture graph")

result = solve_bfs(
    graph, start, map_id="snapshot_fixture", bridge_ids=("b01", "b02"),
    state_key=tuple, is_goal=lambda game_map, state: state == goal,
    successors=lambda game_map, state: game_map[state],
    validate_start_state=validate_start_state,
)
assert result.status == "SOLVED"
assert result.actions == ["SWITCH", "DOWN"]
assert result.metrics.solution_cost == 4
print(json.dumps(result.to_dict(), ensure_ascii=False, allow_nan=False))
```

### JSON từ một lượt chạy nội bộ thật

Đã chạy ngày 15/10/2026 bằng Python 3.12.10 trên graph giả của test runtime:
đường hai hành động cost 6 được chọn thay đường ba hành động cost 3. Các số đo
dưới đây là của đúng lượt này, không phải benchmark Bloxorz hoặc mốc hiệu năng.

```json
{
  "map_id": "fake_graph",
  "algorithm": "BFS",
  "status": "SOLVED",
  "start_state": {
    "mode": "UPRIGHT",
    "cells": [[0, 0]],
    "active": null,
    "bridges": {}
  },
  "actions": ["UP", "RIGHT"],
  "metrics": {
    "search_time_s": 4.140000055485871e-05,
    "peak_memory_bytes": 2288,
    "expanded_nodes": 3,
    "solution_length": 2,
    "solution_cost": 6
  },
  "timeout_s": 60.0,
  "heuristic": null,
  "error": null,
  "schema_version": 1,
  "cost_model": "base1_fragile2_switch1_v1"
}
```

### Kiểm thử

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_bfs.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_bfs_contract.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_runtime.py' -v
python -m unittest discover -s tests/solvers -p 'test_*.py' -v
```

Kết quả ngày 17/10/2026, Python 3.12.10: **69/69 test liên quan trực tiếp đạt,
không skip** = 16 lõi BFS + 5 hợp đồng callable + 17 common + 31 runtime/kết quả.
Các test runtime/kết quả và smoke test tracemalloc gọi `solve_bfs` công khai;
test hợp đồng xác nhận alias cũ vẫn trỏ cùng callable. Không xóa hoặc làm yếu
assertion cũ.

Bao phủ đường ít action khác đường rẻ nhất, parent khi enqueue, chu trình/cạn
frontier, full key khác cầu/active, snapshot giữa tiến trình và round-trip JSON,
validator fixture chấp nhận/từ chối snapshot, metadata bắt buộc/sai, năm status,
metrics, cleanup và input bất biến. Test timeout dùng clock giả; ba smoke test
dùng tracemalloc thật kiểm tra chạy lặp, cleanup sau lỗi và giữ phiên ngoài.
Ví dụ fixture ở trên đã chạy độc lập và xuất được JSON chuẩn.

Kiểm tra mở rộng: **140/140 test solver** và **12/12 test engine cơ bản** đạt,
không skip, qua `unittest discover` riêng cho `tests/solvers` và `tests/engine`.
Lệnh `python -m unittest discover -s tests/integration -t . -v` ghi nhận 23 mục
đạt, hai test khởi chạy GUI thất bại và một module controller không nạp được
do môi trường thiếu `pygame`. Chưa xác nhận GUI hoặc BFS nối engine nâng cao;
fixture không phải bằng chứng lời giải map thật.

### Giới hạn và tích hợp

Callable `solve_bfs` có runtime, kết quả chuẩn và callback validation bắt buộc;
dispatcher chung `solve(game_map, start_state, algorithm, ...)` vẫn do bên tích
hợp cung cấp. Khi tích hợp cần
gắn state_key/is_goal/successors/validator, lấy metadata thật và replay trên
bộ map cơ bản, đối chiếu step_cost và vô nghiệm. TV3 nối worker/GUI và run_id;
TV5 dùng lại runtime cho UCS/A*. Không tạo vòng BFS thứ hai trong wrapper.

Timeout là hợp tác, không dừng callback đang chặn. Tracemalloc theo tiến trình:
lượt search từ chối phiên tracking đã bật; không hỗ trợ solver đo đồng thời
trong một tiến trình. Peak không phải RSS. Chưa kiểm tra luật Bloxorz,
map/replay, GUI hoặc benchmark thật.
