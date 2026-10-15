# Solver: chi phí, API và kết quả

- Phiên bản 1.0. Thành viên 1 phối hợp 3–5; thành viên 4 làm BFS/DFS, thành viên 5 làm UCS/A*.

## 7. HÀM CHI PHÍ VÀ HEURISTIC

- cost = 1 + 2 * F + T
- F: số ô fragile trong next_state.cells không có trong state.cells.
- T: số công tắc soft/heavy thực sự kích hoạt trong bước; không tính số cầu hoặc targets.
- SWITCH có chi phí 1; tách/nhập không cộng phí riêng.
- Chỉ tính cho bước OK/WON; chi phí luôn là số nguyên ≥ 1.
- Engine dùng chung logic xác định kích hoạt cho transition và step_cost, tránh tính khác nhau.
- Mục tiêu: giảm tổng số hành động và phạt thêm việc vào ô dễ vỡ, kích hoạt công tắc. Đây là quy ước tối ưu của nhóm, không phải xác suất rơi.
- BFS tối ưu số hành động, gồm SWITCH.
- UCS/A* tối ưu tổng chi phí.
- DFS không bảo đảm tối ưu.
- Heuristic ban đầu:
- h(state) = 0 nếu là goal, ngược lại = 1
- Heuristic admissible và consistent vì mỗi bước có chi phí ≥ 1, kể cả khi có teleport. Nó yếu nên A* sẽ hoạt động gần UCS. Chỉ thay bằng heuristic mạnh hơn sau khi chứng minh đúng với chi phí, split và teleport.


## 8. API VÀ KẾT QUẢ SOLVER

- solve(game_map, start_state, algorithm,      timeout_s=60.0, cancel_event=None) -> SolverResult
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
- heuristic: "goal_indicator_v1" cho ASTAR; thuật toán khác là null.
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
    "cells": [
      [
        1,
        1
      ]
    ],
    "active": null,
    "bridges": {}
  },
  "actions": [
    "RIGHT",
    "RIGHT"
  ],
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
- Tính T từ các công tắc vừa nhấn sau chuyển động, trước teleport/nhập;
  dùng cùng helper engine cho transition và step_cost.
- Với SWITCH: F=0, T=0. Chỉ gọi step_cost với next_state thực sự do transition tạo.

| Bước hợp lệ | F | T | Chi phí |
| --- | --- | --- | --- |
| Đi trên floor | 0 | 0 | 1 |
| Mới chiếm một ô fragile | 1 | 0 | 3 |
| Kích hoạt một công tắc cầu | 0 | 1 | 2 |
| SWITCH | 0 | 0 | 1 |

- `run_id` do lớp GUI/worker quản lý ngoài JSON chuẩn để loại kết quả cũ.
- Đây là hợp đồng phối hợp; thành viên 4/5 vẫn tự triển khai thuật toán.

## Làm rõ kết quả ERROR và runtime T4 (15/10/2026)

Quy ước triển khai theo kế hoạch T4; cần dùng cùng quy tắc khi TV1/TV3/TV5 tích hợp. Không thay các key hoặc `schema_version=1`: JSON có **11 trường gốc**, metrics có 5 trường.

- Chỉ với `ERROR`, `map_id`, `start_state`, `timeout_s` được là null nếu sai hoặc chưa xác thực được do validation dừng sớm. Giữ các trường đã xác thực; `error` ghi trường/giai đoạn, loại lỗi và lý do. Không dùng initial state/timeout mặc định để thay đầu vào hỏng.
- Các status khác bắt buộc map_id là chuỗi không rỗng, start_state là object snapshot, timeout_s hữu hạn > 0. Timeout nhận int/float, loại bool; NaN/Infinity không xuất vào JSON.
- Validation diễn ra trước fast path start thắng. Start hợp lệ đã thắng trả SOLVED với actions=[] và toàn bộ chỉ số bằng 0, kể cả event đã set; không chạy tìm kiếm hoặc bật đo.
- Khi tìm kiếm, kiểm tra CANCELLED trước TIMEOUT; elapsed >= timeout_s là hết hạn. Guard chạy quanh successors, từng successor kể cả key trùng, sau callback và trước kết luận terminal. Timeout/hủy là hợp tác, không ngắt callback đang chặn.
- expanded_nodes tăng ngay trước mỗi lời gọi successors, kể cả lời gọi ném lỗi; không đếm goal. Lỗi sau đo phải giữ tiến độ.
- Nếu tracemalloc đã bật trước lượt tìm kiếm, trả ERROR trước đo; không reset/stop phiên ngoài. Chạy đo tuần tự; cách ly tiến trình thuộc worker/benchmark khi tích hợp.
- Cleanup trong finally; lỗi cleanup không che lỗi gốc. KeyboardInterrupt/SystemExit vẫn truyền ra ngoài sau cleanup.
- T4 hiện có `_solve_bfs` nội bộ nhận callback/metadata rõ ràng; chưa phải dispatcher solve công khai hoặc bằng chứng validator/engine thật đã chạy.
