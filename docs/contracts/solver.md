# Solver: chi phí, API và kết quả

- Phiên bản 1.0. Thành viên 1 phối hợp 3–5; thành viên 4 làm BFS/DFS, thành viên 5 làm UCS/A\*.

## 7. HÀM CHI PHÍ VÀ HEURISTIC

- cost = 1 + 2 \* F + T
- F: số ô fragile trong next_state.cells không có trong state.cells.
- T: số ô soft mới chiếm, cộng ô heavy mới chiếm nếu next_state đứng thẳng; không tính số cầu/targets hoặc sự kiện split. Công tắc nằm dưới ô đã chiếm ở state cũ không cộng phí.
- SWITCH có chi phí 1; tách/nhập không cộng phí riêng.
- Chỉ tính cho bước OK/WON; chi phí luôn là số nguyên ≥ 1.
- Engine gọi `calculate_step_cost` từ `src/solvers/costs/calc.py`; chỉ có một công thức chi phí.
- Mục tiêu: giảm tổng số hành động và phạt thêm việc vào ô dễ vỡ, kích hoạt công tắc. Đây là quy ước tối ưu của nhóm, không phải xác suất rơi.
- BFS tối ưu số hành động, gồm SWITCH.
- UCS/A\* tối ưu tổng chi phí.
- DFS không bảo đảm tối ưu.
- Chọn heuristic cố định cho lượt giải: có split/teleport hoặc bắt đầu SPLIT dùng goal indicator; có cầu/công tắc không split dùng Manhattan; map tĩnh nhỏ dùng Reverse BFS, map tĩnh lớn hơn 1000 tư thế dùng Manhattan.
- Goal indicator: 0 tại goal, 1 khi chưa thắng; admissible/consistent vì cost >= 1.
- Manhattan: `ceil(min Manhattan distance / 2)`; khối nằm phủ goal có h=1, không còn h=4. Không áp dụng cận hình học này cho teleport.
- Reverse BFS xét cạnh đảo của đồ thị tư thế map tĩnh, vẫn giữ luật fragile, đếm hành động; nếu không có khoảng cách ngược thì fallback Manhattan.
- Trong bộ 18 map: 6 Reverse BFS, 8 Manhattan, 4 goal indicator. Tên JSON giữ tương thích; phải ghi commit/hash nguồn để phân biệt dữ liệu trước/sau `486a584`.

## 8. API VÀ KẾT QUẢ SOLVER

- solve(game_map, start_state, algorithm, timeout_s=60.0, cancel_event=None) -> SolverResult
- algorithm: BFS, DFS, UCS, ASTAR.
- Giải từ snapshot bất biến của trạng thái hiện tại, giữ nguyên cấu hình cầu.
- Cả bốn thuật toán dùng đầy đủ state_key.
- BFS đánh dấu khi đưa vào queue.
- DFS dùng stack và visited; đẩy successors theo thứ tự ngược để ưu tiên lấy UP ra trước.
- UCS/A* lưu best_g, bỏ entry lỗi thời, cập nhật khi tìm được g nhỏ hơn; A* cho phép mở lại trạng thái.
- Priority queue phá hòa bằng bộ đếm tăng dần.
- Kiểm tra goal sau khi lấy nút hợp lệ ra khỏi frontier, trước mở rộng.
- Kiểm tra hủy/timeout mỗi vòng lặp và trong vòng xử lý successors.
- JSON kết quả dùng cấu trúc đầy đủ bên dưới, với các quy ước:
- status: SOLVED, UNSOLVABLE, TIMEOUT, CANCELLED, ERROR.
- Chỉ trả UNSOLVABLE khi frontier hết; timeout không chứng minh vô nghiệm.
- Nếu không SOLVED: actions, solution_length, solution_cost là null; vẫn giữ thống kê đã đo.
- Nếu đầu vào đã thắng: actions=[], length/cost/expanded bằng 0.
- heuristic: ASTAR ghi đúng chiến lược: `goal_indicator_v1`, `reverse_bfs_manhattan_fallback_v1` hoặc `manhattan_orientation_v1`; thuật toán khác là null.
- error: thông báo khi ERROR; còn lại là null.
- Trong JSON, start_state.bridges là object {ID: bool}. Khi nạp lại, chuyển thành tuple theo thứ tự ID đã chốt.
- GUI phát lại từ đúng start_state và map ban đầu, mỗi bước gọi engine.
- Khi giải, khóa thay đổi game hoặc hủy trước khi thay đổi; kết quả phải gắn với lượt giải để tránh áp dụng kết quả cũ.

## JSON kết quả đầy đủ

- Tất cả các trường dưới đây là bắt buộc. Thời gian/bộ nhớ chỉ minh họa, không phải số đo thực.

```json
{
  "schema_version": 1,
  "map_id": "basic_01",
  "algorithm": "BFS",
  "status": "SOLVED",
  "start_state": {
    "mode": "UPRIGHT",
    "cells": [[1, 1]],
    "active": null,
    "bridges": {}
  },
  "actions": ["RIGHT", "RIGHT"],
  "metrics": {
    "search_time_s": 0.001,
    "peak_memory_bytes": 4096,
    "expanded_nodes": 2,
    "solution_length": 2,
    "solution_cost": 2
  },
  "timeout_s": 60.0,
  "cost_model": "base1_fragile2_switch1_v1",
  "heuristic": null,
  "error": null
}
```

## Ràng buộc đầu vào và đo chi phí

- `timeout_s` là số hữu hạn > 0; `cancel_event` cung cấp `is_set()` hoặc là None.
- Snapshot đầu vào phải hợp lệ theo engine; lỗi đầu vào trả ERROR.
- Mỗi vòng kiểm tra CANCELLED trước TIMEOUT; sau đó mới lấy nút/kiểm tra goal.
- Bắt đầu đã thắng được trả SOLVED ngay sau xác thực, không chạy tìm kiếm.
- Không SOLVED: `actions`, `metrics.solution_length`, `metrics.solution_cost` là null.
- ERROR trước khi đo: các số đo là 0; nếu đã đo thì giữ giá trị thu thập được.
- Đặt `new_cells = next_state.cells - state.cells` theo tập tọa độ sau toàn bộ chuyển trạng thái.
- F đếm ô fragile trong new_cells. T đếm ô soft trong new_cells và ô heavy trong new_cells khi next_state đứng thẳng. Ô split không cộng T. Đây là quy ước chi phí, không phải cách xác định sự kiện công tắc của engine.
- Với SWITCH: F=0, T=0. Chỉ gọi step_cost với next_state thực sự do transition tạo.

| Bước hợp lệ                | F   | T   | Chi phí |
| -------------------------- | --- | --- | ------- |
| Đi trên floor              | 0   | 0   | 1       |
| Mới chiếm một ô fragile    | 1   | 0   | 3       |
| Kích hoạt một công tắc cầu | 0   | 1   | 2       |
| SWITCH                     | 0   | 0   | 1       |

- `run_id` do lớp GUI/worker quản lý ngoài JSON chuẩn để loại kết quả cũ.
- Đây là hợp đồng phối hợp; thành viên 4/5 vẫn tự triển khai thuật toán.

## Làm rõ kết quả ERROR và runtime (15/10/2026)

Quy ước triển khai runtime/kết quả; cần dùng cùng quy tắc khi TV1/TV3/TV5 tích hợp. Không thay các key hoặc `schema_version=1`: JSON có **11 trường gốc**, metrics có 5 trường.

- Chỉ với `ERROR`, `map_id`, `start_state`, `timeout_s` được là null nếu sai hoặc chưa xác thực được do validation dừng sớm. Giữ các trường đã xác thực; `error` ghi trường/giai đoạn, loại lỗi và lý do. Không dùng initial state/timeout mặc định để thay đầu vào hỏng.
- Các status khác bắt buộc map_id là chuỗi không rỗng, start_state là object snapshot, timeout_s hữu hạn > 0. Timeout nhận int/float, loại bool; NaN/Infinity không xuất vào JSON.
- Validation diễn ra trước fast path start thắng. Start hợp lệ đã thắng trả SOLVED với actions=[] và toàn bộ chỉ số bằng 0, kể cả event đã set; không chạy tìm kiếm hoặc bật đo.
- Khi tìm kiếm, kiểm tra CANCELLED trước TIMEOUT; elapsed >= timeout_s là hết hạn. Guard chạy quanh successors, từng successor kể cả key trùng, sau callback và trước kết luận terminal. Timeout/hủy là hợp tác, không ngắt callback đang chặn.
- expanded_nodes tăng ngay trước mỗi lời gọi successors, kể cả lời gọi ném lỗi; không đếm goal. Lỗi sau đo phải giữ tiến độ.
- Nếu tracemalloc đã bật trước lượt tìm kiếm, trả ERROR trước đo; không reset/stop phiên ngoài. Chạy đo tuần tự; cách ly tiến trình thuộc worker/benchmark khi tích hợp.
- Cleanup trong finally; lỗi cleanup không che lỗi gốc. KeyboardInterrupt/SystemExit vẫn truyền ra ngoài sau cleanup.
- T4 hiện có `_solve_bfs` nội bộ nhận callback/metadata rõ ràng; chưa phải dispatcher solve công khai hoặc bằng chứng validator/engine thật đã chạy.

## Điểm gọi triển khai dùng chung

- `src.solvers.solve.solve` nhận GameMap/State hoặc map JSON/snapshot JSON.
- `src.solvers.costs.calc.calculate_step_cost(game_map, current_state, next_state, action)` là công thức chuẩn được chọn. `src.engine.rules.step_cost(game_map, state, action, next_state)` chỉ chuyển tiếp tham số.
- UCS/A\* cộng Successor.cost một lần. Mọi thuật toán nhận cùng state_key, is_goal và successors từ engine.
- A\* dùng cùng quy tắc heuristic tại mục 7: goal indicator chỉ dành cho split/teleport; cầu/công tắc không split dùng Manhattan. Reverse BFS chỉ dùng cho map tĩnh nhỏ. UCS không gọi heuristic.
- BFS cung cấp `src.solvers.bfs.solver.solve_bfs`, nhận map/state cùng các keyword bắt buộc `map_id`, `bridge_ids`, `state_key`, `is_goal`, `successors`, `validate_start_state`; `timeout_s=60.0`, `cancel_event=None`. `_solve_bfs` là alias tương thích. Xem [hướng dẫn và ví dụ fixture](../../src/solvers/bfs/README.md). Callable này chưa phải dispatcher chung hoặc bằng chứng validator/engine thật đã chạy.

## API triển khai và kiểm tra dữ liệu

- Ứng dụng/GUI/benchmark gọi `src.solvers.solve.solve(...)`. `_search(...)` trong mỗi thuật toán chỉ tìm kiếm trên callback engine.
- `solve_bfs`, `solve_dfs`, `_solve_ucs` là adapter tương thích callback; tất cả dùng `common/boundary.py` cho validation, runtime, snapshot, cleanup và lỗi JSON.
- Snapshot được chuẩn hóa tại `engine/serialization.py`: cells là mảng tọa độ JSON, bridge flags là object theo ID đã sắp xếp. Chỉ engine xác thực tư thế được đỡ trên map.
- `common/schema.py` kiểm schema và ràng buộc cơ bản dùng chung cho SolverResult, GUI và benchmark. GUI bổ sung đối chiếu request/replay; benchmark bổ sung trường chính xác và điều kiện đo.
- Tên hằng giao tiếp được khai báo tại `src/contracts.py`; placeholder cũ chuyển tiếp sang dispatcher thật.

### Tiền xử lý Reverse BFS

A* dựng đồ thị đảo một lần cho mỗi lượt giải map tĩnh nhỏ, sau khi bắt đầu runtime.
`search_time_s` và `peak_memory_bytes` bao gồm tiền xử lý; `expanded_nodes` chỉ đếm
nút mở rộng của A*, không cộng các tư thế duyệt khi dựng heuristic. Kiểm tra hủy/
timeout trong các vòng dựng đồ thị và BFS ngược; dừng trước tìm kiếm vẫn giữ số đo.
Không dùng cache từ lượt trước trong solver/benchmark. Cache của helper tra cứu
heuristic độc lập không được dùng cho các lượt tìm kiếm có đo. Map động và map tĩnh
lớn không dựng Reverse BFS. Start đã thắng giữ fast path không tiền xử lý.
