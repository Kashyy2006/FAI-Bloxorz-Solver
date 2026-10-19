# src/solvers/dfs

**Lưu gì / làm gì:** Thuật toán DFS, chống lặp và xuất lời giải.

**Phụ trách:** Thành viên 4.

## Trạng thái triển khai

Đã có callable `solve_dfs`, lõi DFS iterative, runtime/kết quả và kiểm thử
trên đồ thị hữu hạn. Chưa load/replay map thật, xác thực snapshot theo luật
hoặc nối dispatcher chung.
Không dùng kết quả đồ thị kiểm thử làm bằng chứng engine/game hoặc benchmark.

## Callable công khai

```python
from src.solvers.dfs.solver import solve_dfs

result = solve_dfs(
    game_map, current_state,
    map_id=map_id, bridge_ids=bridge_ids,
    state_key=state_key, is_goal=is_goal, successors=successors,
    validate_start_state=validate_start_state,
    timeout_s=60.0, cancel_event=cancel_event,
)
payload = result.to_dict()
```

Chữ ký đầy đủ:

```python
solve_dfs(
    game_map, start_state, *, map_id, bridge_ids,
    state_key, is_goal, successors, validate_start_state,
    timeout_s=60.0, cancel_event=None,
) -> SolverResult
```

Các keyword trước `timeout_s` đều bắt buộc; thiếu đối số gây `TypeError` tại
điểm gọi. Giá trị được truyền nhưng sai hoặc callback ném `Exception` trả
`SolverResult` với status `ERROR`. `_solve_dfs` được giữ làm alias tương thích.

Đoạn trên minh họa điểm nối; caller phải cung cấp map, state, callback và
metadata. Khi engine được bàn giao, lấy chúng từ API thật, không giả định
đường import hoặc thuộc tính GameMap chưa có. Thành phần DFS chưa cung cấp
`solve(game_map, start_state, algorithm, ...)` chung cho bốn thuật toán.

- `state_key(state)` trả khóa hashable đầy đủ `(mode, cells, active, bridges)`.
- `is_goal(game_map, state)` xác định goal theo engine.
- `successors(game_map, state)` trả **list** các phần tử có `action/state/cost`,
  chỉ gồm bước OK/WON, theo thứ tự UP, DOWN, LEFT, RIGHT, SWITCH của contract.
  `cost` là số nguyên ≥ 1; DFS cộng chi phí được cung cấp trên đường đã chọn.
- `validate_start_state(game_map, state)` trả bình thường khi hợp lệ, ném lỗi
  có lý do khi sai. Serializer không thay validator; callback test không chứng
  minh luật game thật. Snapshot hiện tại có thể khác initial state của map.
  Khi tích hợp phải cung cấp validator ngữ nghĩa của engine; không dùng no-op.
  Giá trị trả về của validator không được sử dụng.
- `map_id` là chuỗi không rỗng; `bridge_ids` là tuple ID chuỗi không rỗng,
  duy nhất, theo thứ tự từ điển của map, khớp tuple bool của snapshot.
  Dùng `()` chỉ khi map thật không có cầu; không reset cầu về initial_open.
  Callable kiểm tra kiểu/độ dài/thứ tự; bên tích hợp phải bảo đảm đúng ID của map.
- Timeout nhận int/float hữu hạn >0, loại bool; event là None hoặc có `is_set()`.

Lõi `_search(game_map, start_state, *, state_key, is_goal, successors, runtime=None)`
trả `(actions, solution_cost, expanded_nodes)`. Với stack cạn, hai trường đầu
là None; start đã thắng trả `([], 0, 0)`. Lõi trực tiếp truyền lỗi callback ra
ngoài; lớp bọc `solve_dfs` chuyển Exception thành ERROR. Nếu truyền runtime
trực tiếp cho lõi, caller phải gọi `runtime.finish()` trong finally.

### Ví dụ fixture chạy độc lập

Chạy từ gốc repo. Tọa độ là nhãn node của đồ thị kiểm thử, không mô phỏng luật
cầu/split hoặc xác nhận lời giải Bloxorz:

```python
import json
from collections import namedtuple
from types import SimpleNamespace
from src.solvers.dfs.solver import solve_dfs

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

result = solve_dfs(
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

## Quy tắc DFS

- Stack `list`, lấy bằng `pop()`; duyệt `reversed(successors)` trước khi push
  để ưu tiên phần tử đầu theo engine. Không sửa list successors đầu vào.
- `parent` đồng thời là visited: đánh dấu lúc push, mỗi full key chỉ khám phá
  một lần. Giữ parent/chi phí khám phá đầu tiên, không cập nhật vì có đường rẻ hơn.
- Kiểm tra goal lúc pop trước mở rộng, dựng actions bằng common/path.py;
  không lưu cả đường đi trong từng entry, không đệ quy hoặc giới hạn độ sâu.
- Đây là DFS trên đồ thị đánh dấu khi push. Cây parent có thể khác DFS đệ quy
  xử lý từng cạnh khi đồ thị có cạnh chéo. Không bảo đảm ít bước/rẻ nhất.
- Chi phí báo cáo là tổng Successor.cost trên đường được chọn. SWITCH cũng
  tính một action. Thời gian O(V+E), cấu trúc tìm kiếm O(V), không phải chỉ O(độ sâu).

## Status, số đo và dọn tài nguyên

Dùng lại [common](../common/README.md) và [solver contract](../../../docs/contracts/solver.md).
JSON có 11 trường gốc, 5 metrics; algorithm=DFS, heuristic=null, schema_version=1,
cost_model=base1_fragile2_switch1_v1.

| Trường hợp | Kết quả |
| --- | --- |
| Tìm được goal | SOLVED, actions list, length và cost của đường DFS |
| Start hợp lệ đã thắng | SOLVED, actions=[], cả năm metrics=0, kể cả event đã set |
| Stack cạn | UNSOLVABLE, actions/length/cost=null |
| Hủy hoặc hết hạn | CANCELLED hoặc TIMEOUT; hủy ưu tiên, giữ số đo đã có |
| Validation/callback/result/cleanup lỗi | ERROR có giai đoạn, loại lỗi và lý do; solution fields null |

Validation chạy trước fast path start thắng. Chỉ ERROR được có map_id,
start_state hoặc timeout_s=null khi sai/chưa xác thực; giữ các trường đã xác thực.
Không thay đầu vào sai bằng snapshot đầu map hoặc timeout mặc định. Khi cần
chuỗi JSON, dùng `json.dumps(payload, ensure_ascii=False, allow_nan=False)`.

Guard chạy trước pop, sau kiểm tra goal, quanh successors, mỗi successor kể
cả key trùng và trước kết luận cạn stack. Deadline dùng elapsed >= timeout_s.
expanded_nodes tăng ngay trước mỗi lời gọi successors, kể cả lời gọi ném lỗi;
goal không được mở rộng. Lỗi/hủy giữa search giữ số mở rộng đã có.

Timer bắt đầu trước cấu trúc tìm kiếm, dừng trước dựng actions; không gồm
loader, validation/snapshot, replay hoặc serialize. Tracing giữ qua dựng
actions, lấy peak và dọn trong finally. Peak là bộ nhớ Python, không phải RSS.
Thời gian tìm kiếm có overhead tracemalloc; không so với lượt đo không bật tracing.

Chỉ đo tuần tự một solver mỗi tiến trình. Nếu tracer ngoài đang bật, lượt
cần search trả ERROR trước đo, không reset/stop tracer ngoài. Timeout/hủy là
hợp tác, không ngắt callback đang chặn. KeyboardInterrupt/SystemExit truyền
ra sau cleanup; lỗi cleanup không che lỗi gốc. Worker/bộ chạy benchmark phụ trách cách ly
tiến trình; GUI quản lý run_id ngoài JSON chuẩn.

## JSON từ lượt chạy đồ thị kiểm thử thật

Đồ thị: S có UP→A (cost 3), DOWN→B; A có RIGHT→C; C có DOWN→G;
B có RIGHT→G, các cạnh còn lại cost 1. G là goal. DFS trả đường 3 bước,
cost 5 dù có đường 2 bước cost 2. Tọa độ là nhãn node của fixture, không
thể hiện các nước lăn Bloxorz hợp lệ. Validator demo không kiểm tra luật engine.

JSON dưới đây thu từ một lượt `_solve_dfs` dùng perf_counter/tracemalloc thật
trên Python 3.12.10 ngày 15/10/2026. Time/peak thay đổi theo máy/lượt chạy;
đây không phải số liệu benchmark map game.

```json
{
  "map_id": "fake_graph",
  "algorithm": "DFS",
  "status": "SOLVED",
  "start_state": {
    "mode": "UPRIGHT",
    "cells": [[0, 0]],
    "active": null,
    "bridges": {}
  },
  "actions": ["UP", "RIGHT", "DOWN"],
  "metrics": {
    "search_time_s": 4.140000237384811e-05,
    "peak_memory_bytes": 1144,
    "expanded_nodes": 3,
    "solution_length": 3,
    "solution_cost": 5
  },
  "timeout_s": 60.0,
  "heuristic": null,
  "error": null,
  "schema_version": 1,
  "cost_model": "base1_fragile2_switch1_v1"
}
```

## Kiểm thử và bằng chứng

Từ repo root, không cần dependency mới:

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_dfs.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_dfs_contract.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_dfs_runtime.py' -v
python -m unittest discover -s tests/solvers -p 'test_*.py' -v
```

Kết quả ngày 17/10/2026, Python 3.12.10: **87/87 test liên quan đạt, không skip**
qua `python -m unittest tests.solvers.test_TV4_dfs_contract tests.solvers.test_TV4_dfs tests.solvers.test_TV4_dfs_runtime tests.solvers.test_TV4_common tests.solvers.test_TV4_runtime -q`.
Gồm 39 test DFS, 17 common và 31 runtime/kết quả dùng chung với BFS:

- 10 test lõi: thứ tự/độ sâu, goal lúc pop, parent khi push, chu trình/diamond,
  full key, deep chain vượt recursion limit, chi phí, bất biến và lỗi callback.
- 21 test lớp bọc: validation, năm status/JSON, snapshot round-trip bằng kiểu
  test, guard tại deadline/successor trùng/goal/rỗng, metrics và cleanup/lỗi.
- 3 smoke test tracing thật: chạy lặp, lỗi callback và giữ nguyên tracer ngoài.
- 5 test hợp đồng callable: alias tương thích, metadata/callback bắt buộc,
  đường từ snapshot giữ nhánh cầu/active và round-trip full key, validator
  từ chối snapshot sai, metadata cầu sai kể cả khi snapshot đã goal.

Các test runtime/kết quả và smoke test tracing gọi `solve_dfs` công khai;
giữ nguyên assertion cũ. Đường trả về được phát lại trên graph fixture để
kiểm tra từng action và goal. Ví dụ fixture trong README đã chạy độc lập,
trả `SOLVED`, hai action, cost 4 và JSON schema v1.

Kiểm tra mở rộng: **145/145 test solver**, **12/12 test engine cơ bản** đạt,
không skip, qua discovery riêng từng thư mục. Lệnh discovery từ `tests`
hiện chỉ phát hiện nhóm tích hợp: 23 mục đạt, hai test khởi chạy GUI thất bại
và một module controller không nạp được do môi trường thiếu `pygame`.
Chưa xác nhận DFS nối engine nâng cao, GUI hoặc replay map thật.

Kiểm tra trước đây đã xác nhận test bắt được hai mutation trong bộ nhớ:
`pop()` thành `pop(0)` và bỏ `reversed`; không chạy lại mutation trong lượt này.
Không sửa byte source để chạy mutation hoặc skip test tích hợp.

## Tích hợp với engine và GUI

Khi TV1 bàn giao, nối callback/metadata/validator thật và điểm gọi nhóm đã
thống nhất; chạy bốn map cố định, replay từng action bằng transition, đối
chiếu step_cost và full state_key. Kiểm tra snapshot giữa ván/đã thắng,
input bất biến và map vô nghiệm cạn đúng ba state. Bộ cơ bản có cầu rỗng,
chưa chứng minh cơ chế nâng cao, SPLIT hoặc cấu hình cầu thực đã đúng.

TV3 nhận điểm gọi/status/JSON và giới hạn runtime để nối worker/GUI; bộ chạy benchmark nhận
DFS có cùng quy ước đo để chạy benchmark. Không nhận thay engine, GUI,
UCS/A*, không tự reset snapshot hiện tại. Phần triển khai/test/tài liệu DFS
có AI hỗ trợ; giữ ghi nhận này cho phụ lục báo cáo của nhóm.
