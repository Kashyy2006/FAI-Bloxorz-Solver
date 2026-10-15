# src/solvers/common

**Lưu gì / làm gì:** Hợp đồng kết quả, dựng đường đi, timeout/hủy và tiện ích solver chung.

**Phụ trách:** Thành viên 4 phối hợp 3 và 5.

## Kết quả và snapshot

- `result.py`: `SolverMetrics`, `SolverResult.to_dict()` và `snapshot_to_dict`.
- `path.py`: `reconstruct_actions(parent, action_to, goal_key)`.
- JSON có **11 trường gốc**, metrics có 5 trường theo [solver contract](../../../docs/contracts/solver.md).
- Chỉ `ERROR` được có `map_id`, `start_state`, `timeout_s` bằng `None` khi trường đó chưa xác thực được. Các trường đã xác thực giữ nguyên. Không chép NaN/Infinity hoặc tự thay bằng snapshot/timeout mặc định.
- Snapshot helper chỉ chuyển định dạng và kiểm tra sự tương ứng của cầu; validation luật game thuộc engine. `to_dict()` kiểm tra tính nhất quán kết quả, không thay engine validator.

## Runtime T4

`runtime.py` cung cấp `validate_timeout(timeout_s)`, `SearchStopped(status)` và:

```python
SearchRuntime(timeout_s=60.0, cancel_event=None, metrics=None)
```

Mỗi lượt dùng một runtime mới. `metrics` có thể là `SolverMetrics` được lớp bọc giữ để đọc tiến độ khi bị ngắt. Timeout nhận int/float hữu hạn > 0, loại bool/chuỗi/NaN/Infinity; event là None hoặc có `is_set()` callable.

| Thao tác | Trách nhiệm |
| --- | --- |
| `start()` | Từ chối tracing đang bật; bật tracemalloc riêng rồi lấy mốc perf_counter, trước cấu trúc tìm kiếm |
| `check_stop()` | Ném SearchStopped với CANCELLED trước TIMEOUT; elapsed >= timeout là hết hạn |
| `mark_search_stopped()` | Chốt search_time_s một lần khi tìm được goal/cạn frontier, trước dựng actions |
| `finish()` | Chốt thời gian nếu còn thiếu, lấy peak rồi stop tracing do runtime tạo; gọi trong finally, gọi lại không dừng hai lần |

`expanded_nodes` phải tăng ngay trước từng lời gọi successors, không tính goal. Lõi thuật toán cập nhật trực tiếp `runtime.metrics.expanded_nodes`; không đợi hàm tìm kiếm return để lấy số đếm.

Thời gian không gồm validation/snapshot, đọc map, dựng actions, GUI, replay hoặc xuất JSON. Peak là bộ nhớ Python tracemalloc theo dõi tới sau dựng actions, không phải RSS. Timer có chịu ảnh hưởng của tracemalloc. Start hợp lệ đã thắng không bật đo và có time/peak/expanded bằng 0.

Lớp bọc bắt SearchStopped riêng, Exception thành ERROR; giữ metrics đã thu, xóa các trường solution khi không SOLVED. KeyboardInterrupt/SystemExit vẫn truyền ra, nhưng finally vẫn dọn tracing. Nếu cleanup lỗi, giữ cả nguyên nhân tìm kiếm lẫn nguyên nhân cleanup.

### Điều kiện vận hành

Chỉ chạy tuần tự, một solver có đo trong một tiến trình. Nếu tracemalloc đã bật bởi profiler hoặc lượt khác, lượt tìm kiếm trả ERROR trước đo; không reset_peak/stop phiên ngoài. Không hỗ trợ nhiều solver đồng thời trong một tiến trình; worker/benchmark cần cách ly tiến trình khi tích hợp.

Timeout/hủy là hợp tác: đặt guard trước dequeue, quanh successors, mỗi successor kể cả key trùng và trước kết luận terminal. Không ngắt callback engine đang chặn; kiểm tra lại khi callback trả về. `run_id` thuộc GUI/worker, không thêm vào result.

## Kiểm thử

Từ repo root, dùng Python 3.12, không cần dependency mới:

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_runtime.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_common.py' -v
python -m unittest discover -s tests/solvers -p 'test_*.py' -v
```

Runtime/result có test clock/event/tracer kiểm soát được và smoke test tracemalloc thật. Các đồ thị giả kiểm tra quy tắc solver; chưa xác nhận snapshot theo engine, map/replay hoặc GUI. Xem [BFS](../bfs/README.md) cho điểm nối T5 và kết quả nghiệm thu cuối.
