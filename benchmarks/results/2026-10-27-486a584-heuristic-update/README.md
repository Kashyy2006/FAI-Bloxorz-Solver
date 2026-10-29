# Benchmark đồng bộ heuristic ngày 2026-10-27

- Commit nguồn: `486a584388cb2543df228d5cf084788cf4ea5af0`; `code_dirty=true`.
  Trạng thái working tree được ghi tại lúc đo; hash từng file thực thi nằm trong report.json.
- Python: `3.12.6 (tags/v3.12.6:a4a2d2b, Sep  6 2024, 20:11:23) [MSC v.1940 64 bit (AMD64)]`; hệ điều hành: `Windows-10-10.0.19045-SP0`.
- CPU: `Intel64 Family 6 Model 154 Stepping 3, GenuineIntel`; số logical CPU: 16.
- Thời điểm UTC: `2026-10-27T16:02:47.466955+00:00`; không dùng cấu hình máy của phiên báo cáo cũ.
- 18 map × 4 solver × 3 lượt = 216 lượt; timeout 60 giây; spawn riêng và chạy tuần tự.
- Trạng thái: `{'SOLVED': 192, 'UNSOLVABLE': 24}`; readiness issues: 0.
- Đã replay qua engine 192 lời giải SOLVED: đúng goal, length và cost.
- Kiểm tra hash nguồn/map, metadata heuristic, ba lượt/cặp, dữ liệu đường đi ổn định,
  cost A*/UCS và length BFS: đạt. Không dùng expected_solvable để sinh kết quả.
- Phân bố heuristic A*: `{'reverse_bfs_manhattan_fallback_v1': 6, 'manhattan_orientation_v1': 8, 'goal_indicator_v1': 4}`.

## Bảng tổng hợp

Chỉ dùng 16 map có 3/3 lượt SOLVED cho **cả bốn thuật toán**.
Mỗi ô là trung bình cộng của các trung vị theo map; không phải trung vị của toàn bộ lượt.
Length gồm SWITCH; peak là tracemalloc Python, không phải RSS. Thời gian và peak
A* bao gồm tiền xử lý; expanded không gồm đồ thị tiền xử lý.

| Thuật toán | Time (ms) | Peak Python (MiB) | Expanded | Length | Cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| BFS | 362.36 | 0.4224 | 1094.56 | 40.31 | 51.62 |
| DFS | 109.69 | 0.2305 | 369.69 | 166.19 | 183.00 |
| UCS | 396.12 | 0.4831 | 1158.00 | 40.50 | 50.69 |
| ASTAR | 384.47 | 0.4741 | 1121.69 | 40.50 | 50.69 |

## Nhận xét theo phiên đo

Trên 16 map giải được chung, A* và UCS trả cùng chi phí tối ưu. A* mở rộng ít nút hơn UCS trên 11/16 map, nhưng chỉ nhanh hơn trên 6/16 map. Chi phí tính heuristic và tiền xử lý được tính vào thời gian tìm kiếm; giảm số nút mở rộng không bảo đảm giảm thời gian thực thi. DFS nhanh nhất trên 13/16 map trong phiên đo này, nhưng không bảo đảm lời giải ngắn nhất hay chi phí thấp nhất. Các chênh lệch thời gian là quan sát từ ba lượt đo, chưa phải kết luận có ý nghĩa thống kê.

## File bàn giao

- `report.json`, `runs.csv`, `summary.csv`, `readiness.csv`: dữ liệu runner gốc, không sửa sau đo.
- `verification.json`: hash report và các kiểm tra replay/invariant theo từng lượt.
- `per_map_medians.csv`: 72 cặp map/thuật toán, trạng thái, heuristic và trung vị SOLVED (N/A nếu vô nghiệm).
- `aggregate.csv`: trung bình các trung vị trên tập map giải được chung.
- `report_tables.tex`: bảng LaTeX để thay bảng số liệu cũ trong báo cáo; chưa sửa PDF ngoài repo.
- `discussion.tex`: nhận xét so sánh được tính từ chính phiên đo này.
- Biểu đồ PNG/SVG nằm trong thư mục cùng tên ở `benchmarks/charts/`.

Kết quả này thay cho số liệu A* dùng quy tắc cũ khi mô tả phiên bản hiện tại.
Không trộn thời gian/bộ nhớ giữa các cấu hình máy hay các phiên đo.
Không thay đổi trọng số cost, bộ map hoặc tên heuristic JSON trong lượt đồng bộ này.
Executable cũ chưa được build lại và không đại diện cho phiên đo này.

Tái lập phân tích: `python -m benchmarks.analyze --report PATH/report.json --charts CHART_DIR`.
Cần matplotlib để xuất hình; phân tích từ chối source/map không khớp phiên đo.
