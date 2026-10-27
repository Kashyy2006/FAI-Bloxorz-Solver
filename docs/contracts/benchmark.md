# Benchmark và thống kê

- Phiên bản 1.0. Thành viên 4 triển khai bộ đo; thành viên 5 tổng hợp bảng/biểu đồ.

## Chỉ số thống nhất

| Chỉ số | Định nghĩa |
| --- | --- |
| search_time_s | perf_counter từ trước tiền xử lý heuristic/tạo frontier đến khi dừng tìm kiếm; không gồm đọc map, GUI, replay, ghi JSON. |
| expanded_nodes | Số lần gọi successors cho nút hợp lệ; không tính goal/entry lỗi thời. |
| solution_length | len(actions), gồm SWITCH. |
| solution_cost | Tổng step_cost của lời giải. |
| peak_memory_bytes | Đỉnh bộ nhớ Python do tracemalloc theo dõi trong solve; không phải RSS. |

Làm rõ mốc đo ngày 15/10/2026: validation/chuyển snapshot ở trước đo; timer dừng khi xác định goal/cạn frontier/dừng tìm kiếm, trước dựng actions. Tracemalloc tiếp tục theo dõi qua dựng actions, lấy peak và dọn trước xuất JSON. Start hợp lệ đã thắng không khởi động tìm kiếm, cả năm chỉ số bằng 0. Các solver cần dùng cùng mốc đo này khi tích hợp; không so thời gian có/không bật tracemalloc như cùng một điều kiện.

## Quy trình

- Khởi động tracemalloc trước khi tạo cấu trúc tìm kiếm; bật nhất quán cho mọi solver và ghi rõ thời gian có ảnh hưởng của công cụ đo.
- Chạy tuần tự, mỗi lượt trong tiến trình riêng; cùng map và trạng thái đầu.
- Timeout 60 giây; 3 lượt cho mỗi cặp map/solver.
- Lưu từng lượt; tổng hợp bằng trung vị các lượt SOLVED, kèm số lượt mỗi status. Không có lượt thành công thì ghi N/A.
- Bộ map cố định gồm cơ bản, fragile, cầu/công tắc, split và vô nghiệm.
- Báo cáo ghi cấu hình máy, phiên bản Python, phiên bản code và bộ map.

## Dữ liệu bàn giao

- Lưu kết quả từng lượt tại `benchmarks/results/`, kèm map_id, algorithm,
- run_index (1–3), phiên bản code và JSON SolverResult. Bảng tổng hợp có số
- lượt mỗi status, trung vị thời gian/bộ nhớ/nút/độ dài/chi phí của lượt SOLVED.
- Biểu đồ lưu tại `benchmarks/charts/`; ghi rõ đơn vị và không coi TIMEOUT
- là UNSOLVABLE. Nhãn expected_solvable chỉ dùng đối chiếu kiểm thử.

## Đồng bộ heuristic ngày 27/10/2026

Bộ 18 map hiện chọn 6 Reverse BFS, 8 Manhattan và 4 goal indicator cho A*.
Manhattan dùng hiệu chỉnh 1 cho tư thế nằm phủ goal; dữ liệu trước thay đổi này
không được gắn nhãn như số liệu của phiên bản mới. Giữ các phiên đo trong các thư
mục riêng, kèm commit/dirty flag, hash nguồn và metadata heuristic. Chiến lược của
UCS/BFS/DFS là null. Xem [phiên đồng bộ](../../benchmarks/results/2026-10-27-486a584-heuristic-update/README.md).
